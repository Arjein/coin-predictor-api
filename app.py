import eventlet
eventlet.monkey_patch()

import os
from flask import Flask
from config import Config
from extensions import db, socketio, cors
from managers.database_manager import DatabaseManager
from routes.routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app, async_mode='eventlet')
    cors.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)

    return app

app = create_app()

@app.before_first_request
def initialize_database_manager():
    print("✅ Starting Database Manager background tasks...", flush=True)
    DatabaseManager(app, db, socketio)

if __name__ == '__main__':
    port = int(os.getenv('PORT', Config.PORT))
    socketio.run(app, host='0.0.0.0', port=port)