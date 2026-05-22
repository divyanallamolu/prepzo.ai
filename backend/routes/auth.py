import logging

import bcrypt
from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request

from pymongo.errors import PyMongoError

from extensions import get_db, get_db_mode
from utils.env_check import format_exception, missing_required_env
from utils.jwt_utils import create_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
logger = logging.getLogger("prepzo.auth")


def _config_error_response():
    missing = missing_required_env()
    if not missing:
        return None
    logger.error("Auth blocked — missing env vars: %s", ", ".join(missing))
    return (
        jsonify({
            "error": "Server configuration incomplete",
            "missing_env": missing,
            "hint": "Set MONGO_URI, JWT_SECRET_KEY, and FLASK_SECRET_KEY in Vercel project settings.",
        }),
        503,
    )


def _db_error(message: str = "Database unavailable"):
    logger.error("Database error: %s (mode=%s)", message, get_db_mode())
    return jsonify({"error": message, "database_mode": get_db_mode()}), 503


def _server_error(exc: Exception, action: str):
    tb = format_exception(exc)
    logger.error("Auth %s failed:\n%s", action, tb)
    current_app.logger.error("Auth %s failed:\n%s", action, tb)
    return (
        jsonify({
            "error": f"Unable to complete {action}",
            "detail": str(exc)[:200],
        }),
        500,
    )


def _serialize_user(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name", ""),
        "email": doc.get("email", ""),
        "role": doc.get("role", "user"),
        "created_at": doc.get("created_at", ""),
    }


def _token_string(token) -> str:
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return str(token)


@auth_bp.route("/register", methods=["POST"])
def register():
    cfg_err = _config_error_response()
    if cfg_err:
        return cfg_err

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or len(password) < 6:
        return jsonify({"error": "Name, email, and password (6+ chars) required"}), 400

    try:
        db = get_db()
        logger.info("Register attempt for %s (db_mode=%s)", email, get_db_mode())

        if db.users.find_one({"email": email}):
            return jsonify({"error": "Email already registered"}), 409

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        from datetime import datetime, timezone

        user = {
            "name": name,
            "email": email,
            "password": hashed,
            "role": "user",
            "streak": 0,
            "last_practice": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = db.users.insert_one(user)
        user_id = str(result.inserted_id)
        token = _token_string(create_token(user_id, "user"))

        logger.info("Register success for %s (id=%s)", email, user_id)
        return (
            jsonify({
                "token": token,
                "user": _serialize_user({**user, "_id": result.inserted_id}),
            }),
            201,
        )
    except PyMongoError as exc:
        return _db_error(str(exc))
    except Exception as exc:
        return _server_error(exc, "registration")


@auth_bp.route("/login", methods=["POST"])
def login():
    cfg_err = _config_error_response()
    if cfg_err:
        return cfg_err

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    try:
        db = get_db()
        logger.info("Login attempt for %s (db_mode=%s)", email, get_db_mode())

        user = db.users.find_one({"email": email})
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        stored = user.get("password") or ""
        if not stored or not bcrypt.checkpw(
            password.encode("utf-8"), stored.encode("utf-8")
        ):
            return jsonify({"error": "Invalid credentials"}), 401

        token = _token_string(create_token(str(user["_id"]), user.get("role", "user")))
        logger.info("Login success for %s", email)
        return jsonify({"token": token, "user": _serialize_user(user)}), 200
    except PyMongoError as exc:
        return _db_error(str(exc))
    except Exception as exc:
        return _server_error(exc, "login")


@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    cfg_err = _config_error_response()
    if cfg_err:
        return cfg_err

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    try:
        db = get_db()
        user = db.users.find_one({"email": email, "role": "admin"})
        if not user:
            return jsonify({"error": "Invalid admin credentials"}), 401

        stored = user.get("password") or ""
        if not stored or not bcrypt.checkpw(
            password.encode("utf-8"), stored.encode("utf-8")
        ):
            return jsonify({"error": "Invalid admin credentials"}), 401

        token = _token_string(create_token(str(user["_id"]), "admin"))
        return jsonify({"token": token, "user": _serialize_user(user)}), 200
    except PyMongoError as exc:
        return _db_error(str(exc))
    except Exception as exc:
        return _server_error(exc, "admin login")
