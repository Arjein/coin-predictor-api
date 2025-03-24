from sqlalchemy.dialects.postgresql import insert
from models.models import Prediction
import pandas as pd
import os
import requests

HUGGINGFACE_API_URL = os.getenv("HUGGINGFACE_API_URL", "https://arjein-coin-predictor.hf.space/predict")

class PredictionManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.app = db_manager.app
        self.db = db_manager.db

    def run_predictions(self):
        with self.app.app_context():
            engine = self.db.get_engine()
            query = "SELECT * FROM klines ORDER BY open_time DESC LIMIT 2000"
            df = pd.read_sql_query(query, engine)

        df = df.sort_values(by='open_time').reset_index(drop=True)
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
        df['open_time'] = df['open_time'].apply(lambda x: x.isoformat())
        df['symbol'] = df['symbol'].astype('category')
        print('Request Will sent to HF')
        response = requests.post(
            HUGGINGFACE_API_URL,
            json={"data": df.to_dict(orient='records')}
        )
        print('Received Response From HuggingFace:')
        print('Making Predictions Until:', df['open_time'].max())
        
        if response.status_code == 200:
            prediction_result = pd.DataFrame(response.json())
            pred_records = prediction_result.to_dict(orient='records')

            with self.app.app_context():
                stmt = insert(Prediction).values(pred_records)
                stmt = stmt.on_conflict_do_nothing(index_elements=['open_time'])
                self.db.session.execute(stmt)
                self.db.session.commit()

            print("✅ Predictions updated successfully from HuggingFace.")
        else:
            print(f"🚨 Prediction API error: {response.status_code} - {response.text}")