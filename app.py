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
    socketio.init_app(
        app,
        async_mode='eventlet',
        cors_allowed_origins="*",
        ping_interval=10,
        ping_timeout=60,
        logger=True,
        engineio_logger=True
    )
    cors.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)

    return app

app = create_app()

# Ensure initialization when Gunicorn starts (important!)
print("✅ Starting Database Manager background tasks...", flush=True)
db_manager = DatabaseManager(app, db, socketio)

if __name__ == '__main__':
    port = int(os.getenv('PORT', Config.PORT))
    socketio.run(app, host='0.0.0.0', port=port)