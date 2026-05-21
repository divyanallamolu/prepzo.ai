import os
import sys

from flask import Flask, Response, abort, jsonify, send_from_directory
from flask_cors import CORS

from config import Config
from extensions import get_db_mode, init_db
from routes import register_blueprints
from utils.dev_seed import seed_if_empty

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

TEXT_EXTENSIONS = {".html", ".css", ".js", ".json", ".svg", ".txt"}
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
}


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["JSON_AS_ASCII"] = False

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    init_db(app.config["MONGO_URI"])
    mode = get_db_mode()
    if mode == "mongodb":
        app.logger.info("Connected to MongoDB")
    else:
        from extensions import get_db
        seed_if_empty(get_db())
        app.logger.warning("MongoDB unavailable — using in-memory database (data resets on restart)")

    register_blueprints(app)

    @app.route("/uploads/logos/<path:filename>")
    def serve_logo(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    @app.route("/")
    def home():
        return _serve_frontend("auth.html")

    @app.route("/admin")
    @app.route("/admin/")
    def admin_home():
        return _serve_frontend("admin/index.html")

    @app.route("/<path:filename>")
    def frontend_files(filename):
        if filename.startswith("api/"):
            return jsonify({"error": "Not found"}), 404
        return _serve_frontend(filename)

    return app


def _serve_frontend(rel_path: str):
    rel_path = rel_path.replace("\\", "/").lstrip("/")
    if ".." in rel_path.split("/"):
        abort(404)

    if rel_path in ("", "admin", "admin/"):
        rel_path = "admin/index.html"

    full_path = os.path.join(FRONTEND_DIR, rel_path)
    if os.path.isdir(full_path):
        index_path = os.path.join(full_path, "index.html")
        if os.path.isfile(index_path):
            rel_path = f"{rel_path.rstrip('/')}/index.html"
            full_path = index_path
        else:
            abort(404)

    if not os.path.isfile(full_path):
        abort(404)

    ext = os.path.splitext(rel_path)[1].lower()
    mimetype = MIME_TYPES.get(ext, "application/octet-stream")

    if ext in TEXT_EXTENSIONS:
        raw = open(full_path, "rb").read()
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            content = raw.decode("utf-16")
        elif b"\x00" in raw[: min(200, len(raw))]:
            content = raw.decode("utf-16-le")
        else:
            content = raw.decode("utf-8-sig")
        return Response(content, mimetype=mimetype)

    return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path), mimetype=mimetype)


app = create_app()


if __name__ == "__main__":
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    print(f"Prepzo running at http://127.0.0.1:5000")
    print(f"Frontend: {FRONTEND_DIR}")
    app.run(host="127.0.0.1", port=5000, debug=True)
