from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, g, jsonify, request

from extensions import get_db
from services.analytics_service import build_dashboard
from services.streak_service import update_streak
from utils.jwt_utils import token_required

progress_bp = Blueprint("progress", __name__, url_prefix="/api/progress")

PASS_THRESHOLD = 60


@progress_bp.route("", methods=["POST"])
@token_required()
def save_progress():
    db = get_db()
    user_id = g.current_user["sub"]
    data = request.get_json() or {}

    score = float(data.get("score", 0))
    doc = {
        "user_id": user_id,
        "company_id": data.get("company_id", ""),
        "company_name": data.get("company_name", ""),
        "question_id": data.get("question_id", ""),
        "score": score,
        "is_correct": score >= PASS_THRESHOLD,
        "category": data.get("category", ""),
        "difficulty": data.get("difficulty", ""),
        "user_answer": data.get("user_answer", ""),
        "thinking_seconds_used": data.get("thinking_seconds_used", 0),
        "time_spent_seconds": data.get("time_spent_seconds", 0),
        "revealed_early": data.get("revealed_early", False),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    db.progress.insert_one(doc)
    streak_info = update_streak(db, user_id)
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"xp": max(5, int(score // 10))}},
    )
    return jsonify({"message": "Progress saved", "streak": streak_info}), 201


@progress_bp.route("", methods=["GET"])
@token_required()
def get_progress():
    db = get_db()
    user_id = g.current_user["sub"]
    company_id = request.args.get("company_id")
    query = {"user_id": user_id}
    if company_id:
        query["company_id"] = company_id

    records = list(db.progress.find(query).sort("completed_at", -1).limit(100))
    for r in records:
        r["id"] = str(r.pop("_id"))
    return jsonify(records)


@progress_bp.route("/stats", methods=["GET"])
@token_required()
def get_stats():
    db = get_db()
    user_id = g.current_user["sub"]
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$category",
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$score"},
        }},
    ]
    by_category = list(db.progress.aggregate(pipeline))

    total = db.progress.count_documents({"user_id": user_id})
    recent_companies = db.progress.distinct("company_name", {"user_id": user_id})

    user = db.users.find_one({"_id": ObjectId(user_id)})

    timing_pipeline = [
        {"$match": {"user_id": user_id, "time_spent_seconds": {"$gt": 0}}},
        {"$group": {
            "_id": None,
            "avg_time_spent": {"$avg": "$time_spent_seconds"},
            "min_time_spent": {"$min": "$time_spent_seconds"},
            "total_time_spent": {"$sum": "$time_spent_seconds"},
        }},
    ]
    timing = list(db.progress.aggregate(timing_pipeline))
    timing_stats = timing[0] if timing else {}

    fastest = list(db.progress.find(
        {"user_id": user_id, "time_spent_seconds": {"$gt": 0}},
        {"company_name": 1, "time_spent_seconds": 1, "difficulty": 1, "completed_at": 1},
    ).sort("time_spent_seconds", 1).limit(5))
    for f in fastest:
        f["id"] = str(f.pop("_id", ""))

    dash = build_dashboard(db, user_id)
    return jsonify({
        "total_practiced": total,
        "by_category": by_category,
        "recent_companies": recent_companies[:5],
        "streak": user.get("streak", 0) if user else 0,
        "longest_streak": user.get("longest_streak", 0) if user else 0,
        "accuracy": dash.get("accuracy", 0),
        "motivation": dash.get("motivation", []),
        "weekly_activity": dash.get("weekly_activity", []),
        "xp": user.get("xp", 0) if user else 0,
        "timing": {
            "avg_time_spent_seconds": round(timing_stats.get("avg_time_spent", 0), 1),
            "min_time_spent_seconds": timing_stats.get("min_time_spent", 0),
            "total_time_spent_seconds": timing_stats.get("total_time_spent", 0),
            "fastest_completions": fastest,
        },
    })


@progress_bp.route("/leaderboard", methods=["GET"])
def leaderboard():
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$user_id", "total": {"$sum": 1}, "avg_score": {"$avg": "$score"}}},
        {"$sort": {"total": -1}},
        {"$limit": 10},
    ]
    rows = list(db.progress.aggregate(pipeline))
    result = []
    for row in rows:
        user = db.users.find_one({"_id": ObjectId(row["_id"])})
        if user:
            result.append({
                "name": user.get("name", "Anonymous"),
                "total": row["total"],
                "avg_score": round(row.get("avg_score", 0), 1),
                "streak": user.get("streak", 0),
            })
    return jsonify(result)


@progress_bp.route("/bookmarks", methods=["GET"])
@token_required()
def get_bookmarks():
    db = get_db()
    user_id = g.current_user["sub"]
    bookmarks = list(db.bookmarks.find({"user_id": user_id}))
    for b in bookmarks:
        b["id"] = str(b.pop("_id"))
    return jsonify(bookmarks)


@progress_bp.route("/bookmarks", methods=["POST"])
@token_required()
def add_bookmark():
    db = get_db()
    user_id = g.current_user["sub"]
    data = request.get_json() or {}
    question_id = data.get("question_id")
    if not question_id:
        return jsonify({"error": "question_id required"}), 400

    existing = db.bookmarks.find_one({"user_id": user_id, "question_id": question_id})
    if existing:
        return jsonify({"message": "Already bookmarked"})

    doc = {
        "user_id": user_id,
        "question_id": question_id,
        "company_name": data.get("company_name", ""),
        "question_text": data.get("question_text", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.bookmarks.insert_one(doc)
    return jsonify({"message": "Bookmarked"}), 201


@progress_bp.route("/bookmarks/<question_id>", methods=["DELETE"])
@token_required()
def remove_bookmark(question_id):
    db = get_db()
    db.bookmarks.delete_one({
        "user_id": g.current_user["sub"],
        "question_id": question_id,
    })
    return jsonify({"message": "Bookmark removed"})
