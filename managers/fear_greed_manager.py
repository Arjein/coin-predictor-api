import requests
import pandas as pd
from models.models import FearGreedIndex
from sqlalchemy.dialects.postgresql import insert

class FearGreedManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.app = db_manager.app
        self.db = db_manager.db

    def update_index(self):
        url = 'https://api.alternative.me/fng/'
        response = requests.get(url).json()
        records = [{
            'timestamp': int(item['timestamp']) * 1000,
            'value': float(item['value']),
            'value_classification': item['value_classification']
        } for item in response['data']]

        with self.app.app_context():
            stmt = insert(FearGreedIndex).values(records)
            stmt = stmt.on_conflict_do_nothing(index_elements=['timestamp'])
            self.db.session.execute(stmt)
            self.db.session.commit()