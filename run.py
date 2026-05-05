"""
IntimaGuard — Entry Point
Run with: python run.py
Or with gunicorn: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT
"""

import os
import sys

# Add V2 root to path so sdk/ and app/ resolve cleanly
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
