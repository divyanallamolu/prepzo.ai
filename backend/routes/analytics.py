from flask import Blueprint, jsonify

from extensions import get_db
from utils.jwt_utils import admin_required

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@analytics_bp.route("/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    db = get_db()
    return jsonify({
        "users": db.users.count_documents({"role": "user"}),
        "companies": db.companies.count_documents({}),
        "questions": db.questions.count_documents({}),
        "feedback": db.feedback.count_documents({}),
        "sessions": db.progress.count_documents({}),
    })


@analytics_bp.route("/charts", methods=["GET"])
@admin_required
def admin_charts():
    db = get_db()
    by_difficulty = list(db.questions.aggregate([
        {"$group": {"_id": "$difficulty", "count": {"$sum": 1}}},
    ]))
    by_category = list(db.questions.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
    ]))
    by_company = list(db.questions.aggregate([
        {"$group": {"_id": "$company_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]))
    return jsonify({
        "by_difficulty": by_difficulty,
        "by_category": by_category,
        "by_company": by_company,
    })
