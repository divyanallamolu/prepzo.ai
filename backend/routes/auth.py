"""Authentication — register, login, admin login."""
import logging
from datetime import datetime, timezone

import bcrypt
from flask import Blueprint, jsonify, request
from pymongo.errors import PyMongoError

from extensions import DatabaseUnavailableError, get_db
from utils.env_check import missing_env
from utils.jwt_utils import create_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
logger = logging.getLogger("prepzo.auth")


def _serialize_user(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name", ""),
        "email": doc.get("email", ""),
        "role": doc.get("role", "user"),
        "created_at": doc.get("created_at", ""),
    }


def _token_str(token) -> str:
    return token.decode("utf-8") if isinstance(token, bytes) else str(token)


def _config_block():
    missing = missing_env()
    if not missing:
        return None
    return jsonify({
        "error": "Server configuration incomplete",
        "missing_env": missing,
    }), 503


@auth_bp.route("/register", methods=["POST"])
def register():
    blocked = _config_block()
    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or len(password) < 6:
        return jsonify({"error": "Name, email, and password (6+ chars) required"}), 400

    try:
        db = get_db()
        if db.users.find_one({"email": email}):
            return jsonify({"error": "Email already registered"}), 409

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
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
        token = _token_str(create_token(str(result.inserted_id), "user"))
        logger.info("Registered user %s", email)
        return jsonify({"token": token, "user": _serialize_user({**user, "_id": result.inserted_id})}), 201
    except DatabaseUnavailableError as exc:
        logger.error("Register DB unavailable: %s", exc)
        return jsonify({"error": "Database unavailable", "detail": str(exc)[:200]}), 503
    except PyMongoError as exc:
        logger.exception("Register MongoDB error")
        return jsonify({"error": "Database error", "detail": str(exc)[:200]}), 503
    except Exception as exc:
        logger.exception("Register failed")
        return jsonify({"error": "Registration failed", "detail": str(exc)[:200]}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    blocked = _config_block()
    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    try:
        db = get_db()
        user = db.users.find_one({"email": email})
        stored = (user or {}).get("password") or ""
        if not user or not stored or not bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8")):
            return jsonify({"error": "Invalid credentials"}), 401

        token = _token_str(create_token(str(user["_id"]), user.get("role", "user")))
        logger.info("Login success %s", email)
        return jsonify({"token": token, "user": _serialize_user(user)}), 200
    except DatabaseUnavailableError as exc:
        return jsonify({"error": "Database unavailable", "detail": str(exc)[:200]}), 503
    except PyMongoError as exc:
        logger.exception("Login MongoDB error")
        return jsonify({"error": "Database error", "detail": str(exc)[:200]}), 503
    except Exception as exc:
        logger.exception("Login failed")
        return jsonify({"error": "Login failed", "detail": str(exc)[:200]}), 500


@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    blocked = _config_block()
    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    try:
        db = get_db()
        user = db.users.find_one({"email": email, "role": "admin"})
        stored = (user or {}).get("password") or ""
        if not user or not stored or not bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8")):
            return jsonify({"error": "Invalid admin credentials"}), 401

        token = _token_str(create_token(str(user["_id"]), "admin"))
        return jsonify({"token": token, "user": _serialize_user(user)}), 200
    except DatabaseUnavailableError as exc:
        return jsonify({"error": "Database unavailable", "detail": str(exc)[:200]}), 503
    except PyMongoError as exc:
        return jsonify({"error": "Database error", "detail": str(exc)[:200]}), 503
    except Exception as exc:
        logger.exception("Admin login failed")
        return jsonify({"error": "Login failed", "detail": str(exc)[:200]}), 500
