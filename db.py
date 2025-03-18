from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, date, time, timezone
from flask_sqlalchemy import SQLAlchemy
import asyncio
import pandas as pd
from binance_api import BinanceAPIManager
from flask_socketio import SocketIO
import threading
from fear_index_api import FearIndexAPI
from models import FearGreedIndex
from models import Kline, Prediction  # Import your models
import sys 
import os
from dotenv import load_dotenv
from model import BNBPredictor

load_dotenv()
MODEL_PATH = 'models/baseline_model'
device = 'cpu'
predictor = BNBPredictor(path_to_model=MODEL_PATH, device=device)

class DatabaseManager():
    def __init__(self, app, db):
        self.db = db
        self.app = app
        self.final_datetime= pd.to_datetime('2025-03-01', utc=True)
        self.binance_api = BinanceAPIManager()
        self.fear_index_api = FearIndexAPI()
        
        #Setup Database Config
        DATABASE_URI = os.getenv("DATABASE_URL")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.db.init_app(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Setup Database
        with self.app.app_context():
            self.db.create_all()
            # Retrieve the last (most recent) timestamp
            last_record = Kline.query.order_by(Kline.open_time.desc()).first()
            self.final_datetime = pd.to_datetime(last_record.open_time, unit='ms', utc=True) if last_record else self.final_datetime
        print('SELF FINAL TIMESTAMP: ', self.final_datetime)
        self.update_klines()
        self.update_fear_greed_index()
        ##########self.socketio.start_background_task(self.binance_api.start_stream, self, self.socketio)
        threading.Thread(target=self.binance_api.start_stream, args=(self,self.socketio,)).start()
        self.make_predictions()
        
    def make_predictions(self):
        with self.app.app_context():
            engine = self.db.get_engine()
            query = "SELECT * FROM klines ORDER BY open_time DESC LIMIT 2000"
            df = pd.read_sql_query(query, engine)
        df = df.sort_values(by='open_time').reset_index(drop=True)
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
        df['symbol'] = df['symbol'].astype('category')
        print('Making Predictions Until: ', pd.to_datetime(df.open_time.max(), unit='ms', utc=True))
        df = df.drop(columns=['id', 'close_time'])
        prediction_result = predictor.predict(df, preprocess=True)
        pred_records = prediction_result.to_dict(orient='records')
        
        # Insert predictions to database
        with self.app.app_context():
            #print('Inserting: ', prediction_result[-5:])
            stmt = insert(Prediction).values(pred_records)
            stmt = stmt.on_conflict_do_nothing(index_elements=['open_time'])
            self.db.session.execute(stmt)
            self.db.session.commit()
            print(f"✅ Inserted Prediction records into the database.")


        
    def update_klines(self): 
        current = pd.to_datetime(datetime.now(), utc=True).floor('5min')
        print(f"Fetching Interval: {self.final_datetime} --> {current}")
        df = self.binance_api.get_spot_data('BNBUSDT', '5m', self.final_datetime, current)
        df = df.drop(columns='datetime')
        records = df.to_dict(orient='records')
        
        # Convert current time to milliseconds
        current_ts = int(current.timestamp() * 1000)
        
        # Filter out records where the candle is not closed
        filtered_records = [r for r in records if r['close_time'] <= current_ts]
        print(f"Filtered out {len(records) - len(filtered_records)} incomplete records")
        
        with self.app.app_context():
            stmt = insert(Kline).values(filtered_records)
            stmt = stmt.on_conflict_do_nothing(index_elements=['open_time'])
            self.db.session.execute(stmt)
            self.db.session.commit()
            print(f"✅ Inserted {len(filtered_records)} records into the database.")
            
            last_record = Kline.query.order_by(Kline.open_time.desc()).first()
            self.final_datetime = pd.to_datetime(last_record.open_time, unit='ms', utc=True) if last_record else self.final_datetime
            print(f"Last timestamp in DB: {self.final_datetime}")
        
    def update_fear_greed_index(self):
        df = self.fear_index_api.get_fear_greed_index()
        records = df.to_dict(orient='records')
        with self.app.app_context():
            stmt = insert(FearGreedIndex).values(records)
            stmt = stmt.on_conflict_do_nothing(index_elements=['timestamp'])
            self.db.session.execute(stmt)
            self.db.session.commit()
            print(f"✅ Inserted {len(records)} records into the database.")



    def insert_single_kline(self, kline):
        with self.app.app_context():
            # Add to Database
            stmt = insert(Kline).values(kline)
            stmt = stmt.on_conflict_do_nothing(index_elements=['open_time'])
            self.db.session.execute(stmt)
            self.db.session.commit()
            print(f"✅ Inserted Retrieved kline records into the database.")
            self.final_datetime = pd.to_datetime(kline['open_time'], unit='ms', utc=True)