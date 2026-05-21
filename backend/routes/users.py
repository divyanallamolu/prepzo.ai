from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, g, jsonify

from extensions import get_db
from utils.jwt_utils import admin_required, token_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("/me", methods=["GET"])
@token_required()
def get_profile():
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(g.current_user["sub"])})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "user"),
        "streak": user.get("streak", 0),
        "last_practice": user.get("last_practice"),
    })


@users_bp.route("", methods=["GET"])
@admin_required
def list_users():
    db = get_db()
    users = []
    for u in db.users.find({"role": {"$ne": "admin"}}).sort("created_at", -1):
        users.append({
            "id": str(u["_id"]),
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "role": u.get("role", "user"),
            "streak": u.get("streak", 0),
            "created_at": u.get("created_at", ""),
        })
    return jsonify(users)


@users_bp.route("/<user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    db = get_db()
    try:
        oid = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user id"}), 400
    db.users.delete_one({"_id": oid, "role": {"$ne": "admin"}})
    db.progress.delete_many({"user_id": user_id})
    db.bookmarks.delete_many({"user_id": user_id})
    return jsonify({"message": "User deleted"})
