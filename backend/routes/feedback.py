from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, g, jsonify, request

from extensions import get_db
from utils.jwt_utils import admin_required, token_required

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


@feedback_bp.route("", methods=["POST"])
@token_required()
def submit_feedback():
    db = get_db()
    data = request.get_json() or {}
    doc = {
        "user_id": g.current_user["sub"],
        "type": data.get("type", "general"),
        "rating": data.get("rating", 0),
        "message": data.get("message", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if not doc["message"]:
        return jsonify({"error": "Message required"}), 400
    result = db.feedback.insert_one(doc)
    return jsonify({"id": str(result.inserted_id), "message": "Feedback submitted"}), 201


@feedback_bp.route("", methods=["GET"])
@admin_required
def list_feedback():
    db = get_db()
    items = []
    for f in db.feedback.find().sort("created_at", -1).limit(200):
        user = db.users.find_one({"_id": ObjectId(f["user_id"])}) if f.get("user_id") else None
        items.append({
            "id": str(f["_id"]),
            "type": f.get("type", ""),
            "rating": f.get("rating", 0),
            "message": f.get("message", ""),
            "user_name": user.get("name", "Unknown") if user else "Unknown",
            "created_at": f.get("created_at", ""),
        })
    return jsonify(items)
