from flask import Flask, jsonify
from flask_cors import CORS
from db import DatabaseManager, Kline, Prediction
import pandas as pd
import json
from flask_sqlalchemy import SQLAlchemy
from models import db
import os
app = Flask(__name__)
main_app = DatabaseManager(app, db)
CORS(main_app.app)


@main_app.app.route('/candles', methods=['GET'])
def get_candles():
    with main_app.app.app_context():
        last_1000_desc = Kline.query.order_by(Kline.open_time.desc()).limit(1000).all()
        # Reverse the list to have ascending order (oldest first)
        klines = list(reversed(last_1000_desc))
        return jsonify([{
            "time": k.open_time,
            "open": k.open,
            "high": k.high,
            "low": k.low,
            "close": k.close,
            "volume": k.volume
        } for k in klines])
    
@main_app.app.route('/forecasts', methods=['GET'])
def get_predictions():
    with main_app.app.app_context():
        preds = Prediction.query.all()
        #print('Predictions:', preds)
        return jsonify([{
            "time": p.open_time,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
        } for p in preds])


if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=5000)
    #main_app.socketio.run(main_app.app, debug=True, host='0.0.0.0', port=5001)
    
