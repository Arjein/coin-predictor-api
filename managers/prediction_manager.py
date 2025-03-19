from services.predictor import BNBPredictor
from sqlalchemy.dialects.postgresql import insert
from models.models import Prediction
import pandas as pd
import os

class PredictionManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.app = db_manager.app
        self.db = db_manager.db
        model_path = os.getenv("MODEL_PATH", "trained_models/baseline_model")
        self.predictor = BNBPredictor(path_to_model=model_path, device='cpu')

    def run_predictions(self):
        with self.app.app_context():
            engine = self.db.get_engine()
            query = "SELECT * FROM klines ORDER BY open_time DESC LIMIT 2000"
            df = pd.read_sql_query(query, engine)

        df = df.sort_values(by='open_time').reset_index(drop=True)
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
        df['symbol'] = df['symbol'].astype('category')

        print('Making Predictions Until:', df['open_time'].max())

        prediction_result = self.predictor.predict(df, preprocess=True)
        pred_records = prediction_result.to_dict(orient='records')

        with self.app.app_context():
            stmt = insert(Prediction).values(pred_records)
            stmt = stmt.on_conflict_do_nothing(index_elements=['open_time'])
            self.db.session.execute(stmt)
            self.db.session.commit()
            print(f"✅ Inserted {len(pred_records)} prediction records.")