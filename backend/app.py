import os
import threading

from flask import Flask
from flask_cors import CORS
from .database.mongo_connection import get_db
from .database.init_db import initialize_database
from .api.routes import register_routes
from .pipeline.scheduler import start_scheduler

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])
app.url_map.strict_slashes = False
# Force DB connection and initialize schema at startup
get_db()
initialize_database()

register_routes(app)

if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or __name__ != "__main__":
    # Start the scheduler in a daemon thread so it runs in the background
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

if __name__ == "__main__":
    app.run(debug=True)
