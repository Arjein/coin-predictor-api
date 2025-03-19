from flask import jsonify
from models.models import Kline, Prediction

def register_routes(app):
    @app.route('/')
    def index():
        return "Flask-SocketIO running with eventlet!"

    @app.route('/candles')
    def get_candles():
        klines = Kline.query.order_by(Kline.open_time.desc()).limit(100).all()
        klines.reverse()
        return jsonify([{
            "time": k.open_time,
            "open": k.open,
            "high": k.high,
            "low": k.low,
            "close": k.close,
            "volume": k.volume
        } for k in klines])

    @app.route('/forecasts')
    def get_forecasts():
        preds = Prediction.query.order_by(Prediction.open_time.desc()).limit(100).all()
        preds = list(reversed(preds))

        return jsonify([{
            "time": p.open_time,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
        } for p in preds])