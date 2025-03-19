from extensions import db

class Kline(db.Model):
    __tablename__ = 'klines'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String, nullable=False)
    open_time = db.Column(db.BigInteger, unique=True, nullable=False)
    close_time = db.Column(db.BigInteger, nullable=False)
    volume = db.Column(db.Float, nullable=False)
    quote_asset_volume = db.Column(db.Float, nullable=False)
    number_of_trades = db.Column(db.Float, nullable=False)
    taker_buy_base_volume = db.Column(db.Float, nullable=False)
    taker_buy_quote_volume = db.Column(db.Float, nullable=False)
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)

class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    open_time = db.Column(db.BigInteger, unique=True, nullable=False)
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)

class FearGreedIndex(db.Model):
    __tablename__ = 'fear_greed_index'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.BigInteger, unique=True, nullable=False)
    value = db.Column(db.Float, nullable=False)
    value_classification = db.Column(db.String, nullable=False)