from datetime import datetime, timezone

import bcrypt
from bson import ObjectId
from flask import Blueprint, jsonify, request

from pymongo.errors import PyMongoError

from extensions import get_db
from utils.jwt_utils import create_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _db_error():
    return jsonify({"error": "Database unavailable. Restart the server or start MongoDB."}), 503


def _serialize_user(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name", ""),
        "email": doc.get("email", ""),
        "role": doc.get("role", "user"),
        "created_at": doc.get("created_at", ""),
    }


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or len(password) < 6:
        return jsonify({"error": "Name, email, and password (6+ chars) required"}), 400

    try:
        db = get_db()
        if db.users.find_one({"email": email}):
            return jsonify({"error": "Email already registered"}), 409

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
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
        token = create_token(user_id, "user")
        return jsonify({"token": token, "user": {**_serialize_user({**user, "_id": result.inserted_id})}}), 201
    except PyMongoError:
        return _db_error()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    try:
        db = get_db()
        user = db.users.find_one({"email": email})
        if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_token(str(user["_id"]), user.get("role", "user"))
        return jsonify({"token": token, "user": _serialize_user(user)})
    except PyMongoError:
        return _db_error()


@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    try:
        db = get_db()
        user = db.users.find_one({"email": email, "role": "admin"})
        if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return jsonify({"error": "Invalid admin credentials"}), 401

        token = create_token(str(user["_id"]), "admin")
        return jsonify({"token": token, "user": _serialize_user(user)})
    except PyMongoError:
        return _db_error()
