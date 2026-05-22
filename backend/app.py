"""Prepzo Flask API — production application factory."""
import logging
import os
import sys

from flask import Flask, Response, abort, jsonify, request, send_from_directory
from flask_cors import CORS

from config import Config
from extensions import DatabaseUnavailableError, get_db, init_db
from routes import register_blueprints
from services.seed_service import ensure_seeded
from utils.env_check import missing_env

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["JSON_AS_ASCII"] = False
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    )

    @app.before_request
    def cors_preflight():
        if request.method == "OPTIONS" and request.path.startswith("/api"):
            return Response(status=204)

    @app.after_request
    def cors_headers(response):
        if request.path.startswith("/api"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        return response

    missing = Config.validate()
    if missing:
        app.logger.warning("Missing env: %s", ", ".join(missing))
    else:
        try:
            init_db(app.config["MONGO_URI"])
            ensure_seeded(get_db())
            app.logger.info("Prepzo API ready — MongoDB Atlas")
        except Exception as exc:
            app.logger.error("Startup failed: %s", exc)

    register_blueprints(app)

    @app.errorhandler(DatabaseUnavailableError)
    def db_err(err):
        return jsonify({"error": "Database unavailable", "detail": str(err)[:300]}), 503

    @app.errorhandler(Exception)
    def unhandled(err):
        if request.path.startswith("/api"):
            app.logger.exception("API error %s", request.path)
            return jsonify({"error": "Internal server error"}), 500
        raise err

    if not os.environ.get("VERCEL"):
        _local_static(app)

    return app


def _local_static(app: Flask):
    @app.route("/")
    def home():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/<path:path>")
    def static_files(path):
        if path.startswith("api/"):
            abort(404)
        full = os.path.join(FRONTEND_DIR, path)
        if os.path.isfile(full):
            return send_from_directory(FRONTEND_DIR, path)
        if not path.endswith(".html") and os.path.isfile(full + ".html"):
            return send_from_directory(FRONTEND_DIR, path + ".html")
        abort(404)


app = create_app()

if __name__ == "__main__":
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    print("Prepzo → http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
