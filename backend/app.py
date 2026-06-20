import logging
import os
from pathlib import Path

from flask import Flask

from backend.routes.vendor_routes import vendor_bp

UPLOAD_FOLDER = Path(os.environ.get("UPLOAD_FOLDER", "backend/uploads")).resolve()
ALLOWED_EXTENSIONS = {"pdf"}

if not UPLOAD_FOLDER.exists():
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
    app.register_blueprint(vendor_bp)
    logger.info("TPRM backend initialized")
    return app


app = create_app()

@app.route("/")
def home():
    return {
        "status": "running",
        "service": "TPRM Backend"
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("FLASK_PORT", 5000)), debug=False)
