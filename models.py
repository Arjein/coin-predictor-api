from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class Kline(db.Model):
    __tablename__ = 'klines'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String,nullable=False)
    open_time = db.Column(db.BigInteger, nullable=False, unique=True)
    close_time = db.Column(db.BigInteger, nullable=False)
    volume = db.Column(db.Float,nullable=False)
    quote_asset_volume = db.Column(db.Float,nullable=False)
    number_of_trades = db.Column(db.Float,nullable=False)
    taker_buy_base_volume = db.Column(db.Float,nullable=False)
    taker_buy_quote_volume = db.Column(db.Float,nullable=False)
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)
    

    def __repr__(self):
        return f"<Kline {self.open_time}>"
    

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    # BU SORUN CIKARABILIR
    id = db.Column(db.Integer, primary_key=True)
    # When the prediction is meant to be applied (you can store it as a Unix timestamp)
    open_time = db.Column(db.BigInteger, nullable=False, unique=True)
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)
    def __repr__(self):
        return f"<Prediction {self.open_time}>"
    
    

    
class FearGreedIndex(db.Model):
    __tablename__ = 'fear_greed_index'
    
    # BU SORUN CIKARABILIR
    id = db.Column(db.Integer, primary_key=True)
    # When the prediction is meant to be applied (you can store it as a Unix timestamp)
    timestamp = db.Column(db.BigInteger, nullable=False, unique=True)
    
    value = db.Column(db.Float, nullable=False)
    value_classification = db.Column(db.String, nullable=False)


    
    def __repr__(self):
        return f"<Feat_Greed_Index {self.value}>"