from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from sqlalchemy.dialects.postgresql import insert
import requests
import pandas as pd
import time
import asyncio
import websockets
import json
from utils.preprocessing import check_time_series, impute_missing_values_t_s
import websocket

class BinanceManager():
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.app = db_manager.app
        self.db = db_manager.db
        self.socketio = db_manager.socketio

    
    def binance_kline_stream(self):
        url = "wss://stream.binance.com:9443/ws/bnbusdt@kline_5m"
        ws = websocket.WebSocket()

        try:
            ws.connect(url)
            print("✅ Successfully connected to Binance WebSocket", flush=True)
        except Exception as e:
            print("❌ WebSocket connection failed:", e, flush=True)
            return  # terminate if connection fails

        try:
            while True:
                message = ws.recv()
                data = json.loads(message)
                kline = data.get('k', {})
                kline_update = {
                    'symbol': kline.get('s'),
                    'open_time': kline.get('t'),
                    'close_time': kline.get('T'),
                    'volume': kline.get('v'),
                    'quote_asset_volume': kline.get('q'),
                    'number_of_trades': kline.get('n'),
                    'taker_buy_base_volume': kline.get('V'),
                    'taker_buy_quote_volume': kline.get('Q'),
                    'open': kline.get('o'),
                    'high': kline.get('h'),
                    'low': kline.get('l'),
                    'close': kline.get('c'),
                    'is_closed': kline.get('x', False)
                }

                yield kline_update

        except websocket.WebSocketException as e:
            print("WebSocket Exception:", e)
        finally:
            ws.close()
    
    def stream_klines(self):
        for kline_update in self.binance_kline_stream():
            self.socketio.emit('kline_update', kline_update)

            if kline_update.get('is_closed'):
                kline_update.pop("is_closed")
                self.db_manager.insert_single_kline(kline_update)
                print('✅ Kline inserted into Database')

            self.socketio.sleep(0)  # Cooperative sleep



    def get_spot_data(self, symbol, interval, start_date, end_date, chunk_size=1000):
        
        # Convert dates to milliseconds
        start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
        end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)
        
        klines = []
        current_ts = start_ts
        kline_url = "https://api.binance.com/api/v3/klines"
        
        print(f"Fetching {symbol} data from {start_date}:{start_ts} to {end_date}{end_ts} at {interval} intervals...")
        
        
        while current_ts < end_ts:
            print(f"INLOOP: Fetching {symbol} data from {pd.to_datetime(current_ts, unit='ms', utc=True)} to {pd.to_datetime(end_ts, unit='ms', utc=True)}")
            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": current_ts,
                "endTime": end_ts,
                "limit": chunk_size
            }
            try:
                response = requests.get(kline_url, params=params)
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                break
            
            data = response.json()
            if not data:
                break
            
            klines.extend(data)
            last_open_time = data[-1][0]
            current_ts = last_open_time + 1  # Move past the last candle
            time.sleep(1)  # Respect rate limits
            
        print(f"Total klines fetched: {len(klines)}")
        # Define columns as provided by Binance
        columns = ["open_time", "open", "high", "low", "close", "volume", 
                "close_time", "quote_asset_volume", "number_of_trades", 
                "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"]
        
        df = pd.DataFrame(klines, columns=columns)
        
        # Drop the "ignore" column
        df = df.drop(columns=["ignore"])

        # Convert numeric columns to appropriate types
        numeric_cols = ["open", "high", "low", "close", "volume", "quote_asset_volume", 
                        "number_of_trades", "taker_buy_base_volume", "taker_buy_quote_volume"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
        
        # Add the item_id column with the symbol value and set its type to 'category'
        df["symbol"] = symbol
        df["symbol"] = df["symbol"].astype("category")
        
        # REMOVED DATETIME
        #df['datetime'] = pd.to_datetime(df["open_time"], unit='ms', utc=True)
        # Reorder the columns:
        # Timestamp column: "open_time"
        # Item_id column: "item_id"
        # Control columns: "close_time", "volume", "quote_asset_volume", "number_of_trades", "taker_buy_base_volume", "taker_buy_quote_volume"
        # OHLC columns: "open", "high", "low", "close"
        new_order = [
            "symbol",      #  Symbol
            #"datetime",
            "open_time",    # Timestamp column
            "close_time",   
            "volume",       # Controls
            "quote_asset_volume", 
            "number_of_trades", 
            "taker_buy_base_volume", 
            "taker_buy_quote_volume",
            "open",         # OHLC columns
            "high", 
            "low", 
            "close"
        ]
        
        df = df[new_order]
        #print(f'Open times (Before Processing): {df.open_time}')
        check_time_series(df)
        #print(f'Open times (After CheckTimeSeries): {df.open_time}')
        df = impute_missing_values_t_s(df)
        #print(f'Open times (After Imputing): {df.open_time}')
        check_time_series(df)
        #print(f'Open times (After Second CheckTimeSeries): {df.open_time}')
        return df


