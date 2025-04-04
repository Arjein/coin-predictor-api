import os
from datetime import datetime
import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from flask_socketio import SocketIO
from managers.binance_manager import BinanceManager
from managers.fear_greed_manager import FearGreedManager
from managers.prediction_manager import PredictionManager
from models.models import Kline, Prediction, FearGreedIndex

class DatabaseManager:
    def __init__(self, app, db, socketio):
        self.app = app
        self.db = db
        self.socketio = socketio

        self.binance_manager = BinanceManager(self)
        self.fear_greed_manager = FearGreedManager(self)
        self.prediction_manager = PredictionManager(self)

        with self.app.app_context():
            self.db.create_all()
            last_kline = Kline.query.order_by(Kline.open_time.desc()).first()
            if last_kline:
                self.final_datetime = pd.to_datetime(last_kline.open_time, unit='ms', utc=True)
            else:
                self.final_datetime = pd.to_datetime('2025-03-01', utc=True)

        print(f'✅ Last Kline timestamp: {self.final_datetime}')
        
        self.socketio.start_background_task(self._initial_load)
        self.socketio.start_background_task(self._prediction_loop)
        self.socketio.start_background_task(self.binance_manager.stream_klines)
        

    def _prediction_loop(self):
        """Run predictions every 5 minutes."""
        print('Prediction Loop Started')
        while True:
            try:
                print('Making Predictions')
                self.prediction_manager.run_predictions()
                print("✅ Predictions updated")
            except Exception as e:
                print("❌ Prediction error:", e)
            print('Prediction Sleeping')
            self.socketio.sleep(300)  # wait 5 minutes


    def _initial_load(self):
        """One‑time historical data + fear index at startup."""
        self.update_klines()
        self.update_fear_greed_index()
        print("✅ Initial load complete")
    


    def update_klines(self):
        current = pd.to_datetime(datetime.now(), utc=True).floor('5min')
        df = self.binance_manager.get_spot_data('BNBUSDT', '5m', self.final_datetime, current)
        df = df.drop(columns='datetime')
        records = df.to_dict(orient='records')

        current_ts = int(current.timestamp() * 1000)
        filtered_records = [r for r in records if r['close_time'] <= current_ts]
        
        with self.app.app_context():
            stmt = insert(Kline).values(filtered_records)
            stmt = stmt.on_conflict_do_nothing(index_elements=['open_time'])
            self.db.session.execute(stmt)
            self.db.session.commit()

            print(f"✅ Inserted {len(filtered_records)} klines into DB.")

            total_rows = self.db.session.query(Kline).count()
            if total_rows > 5000:
                self.cleanup_klines()

            last_record = Kline.query.order_by(Kline.open_time.desc()).first()
            self.final_datetime = pd.to_datetime(last_record.open_time, unit='ms', utc=True)
            print(f"✅ Updated latest timestamp: {self.final_datetime}")

    def cleanup_klines(self):
        with self.app.app_context():
            subquery = self.db.session.query(Kline.id).order_by(Kline.open_time.desc()).limit(5000).subquery()
            delete_stmt = Kline.__table__.delete().where(~Kline.id.in_(subquery))
            result = self.db.session.execute(delete_stmt)
            self.db.session.commit()
            print(f"🗑️ Deleted {result.rowcount} old kline records, keeping latest 5000.")

    def update_fear_greed_index(self):
        self.fear_greed_manager.update_index()

    def make_predictions(self):
        self.prediction_manager.run_predictions()

    def insert_single_kline(self, kline):
        with self.app.app_context():
            stmt = insert(Kline).values(kline)
            stmt = stmt.on_conflict_do_nothing(index_elements=['open_time'])
            self.db.session.execute(stmt)
            self.db.session.commit()
            self.final_datetime = pd.to_datetime(kline['open_time'], unit='ms', utc=True)
            print(f"✅ Single Kline inserted. New timestamp: {self.final_datetime}")