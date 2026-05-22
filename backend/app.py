"""Prepzo Flask API application."""
import logging
import os
import sys

from flask import Flask, Response, jsonify, request
from flask_cors import CORS

from config import Config
from extensions import DatabaseUnavailableError, init_db
from routes import register_blueprints
from utils.env_check import env_flags, missing_env

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
        app.logger.warning("Missing environment variables: %s", ", ".join(missing))
    else:
        try:
            init_db(app.config["MONGO_URI"])
            app.logger.info("Prepzo API ready — MongoDB Atlas connected")
        except Exception as exc:
            app.logger.error("MongoDB initialization failed: %s", exc)

    register_blueprints(app)

    @app.errorhandler(DatabaseUnavailableError)
    def handle_db_unavailable(err):
        return jsonify({"error": "Database unavailable", "detail": str(err)[:300]}), 503

    @app.errorhandler(404)
    def handle_not_found(err):
        if request.path.startswith("/api"):
            return jsonify({"error": "Not found"}), 404
        return err

    @app.errorhandler(Exception)
    def handle_exception(err):
        if request.path.startswith("/api"):
            app.logger.exception("Unhandled error on %s", request.path)
            return jsonify({"error": "Internal server error", "detail": str(err)[:200]}), 500
        raise err

    if not os.environ.get("VERCEL"):
        _register_local_frontend(app)

    return app


def _register_local_frontend(app: Flask):
    """Serve static frontend when running locally (not on Vercel)."""
    from flask import abort, send_from_directory

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
        if path.endswith(".html") or "." not in os.path.basename(path):
            candidate = path if path.endswith(".html") else f"{path}.html"
            if os.path.isfile(os.path.join(FRONTEND_DIR, candidate)):
                return send_from_directory(FRONTEND_DIR, candidate)
        abort(404)


app = create_app()


if __name__ == "__main__":
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    print("Prepzo local server: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
