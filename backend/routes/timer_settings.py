"""
Timer settings — prep phase (mandatory 45s), answer phase by difficulty, 30min quiz max.
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from extensions import get_db
from utils.jwt_utils import admin_required

timer_bp = Blueprint("timer", __name__, url_prefix="/api/timer")

# Fixed professional defaults (seconds)
PREP_SECONDS = 45  # mandatory thinking before typing
ANSWER_BY_DIFFICULTY = {"Easy": 45, "Medium": 90, "Hard": 120}
QUIZ_MAX_SECONDS = 1800  # 30 minutes

DEFAULT_CONFIG = {
    "prep_seconds": PREP_SECONDS,
    "answer_by_difficulty": ANSWER_BY_DIFFICULTY,
    "quiz_max_seconds": QUIZ_MAX_SECONDS,
    "auto_next_on_timeout": True,
    "show_ideal_after_submit_only": True,
    "defaults": {
        "prep_seconds": PREP_SECONDS,
        "quiz_max_seconds": QUIZ_MAX_SECONDS,
        "auto_next_on_timeout": True,
    },
    "by_difficulty": {
        "Easy": {"answer_seconds": 45},
        "Medium": {"answer_seconds": 90},
        "Hard": {"answer_seconds": 120},
    },
    "by_company": {},
}


def _get_config_doc(db):
    doc = db.timer_settings.find_one({"type": "config"})
    if not doc:
        doc = {"type": "config", **DEFAULT_CONFIG}
        db.timer_settings.insert_one({**doc, "updated_at": datetime.now(timezone.utc).isoformat()})
    return doc


def resolve_settings(db, company_id: str = "", difficulty: str = "Medium") -> dict:
    config = _get_config_doc(db)
    prep = int(config.get("prep_seconds", PREP_SECONDS))
    quiz_max = int(config.get("quiz_max_seconds", QUIZ_MAX_SECONDS))

    by_diff = dict(ANSWER_BY_DIFFICULTY)
    for k, v in (config.get("by_difficulty") or {}).items():
        if isinstance(v, dict) and v.get("answer_seconds") is not None:
            by_diff[k] = int(v["answer_seconds"])
    answer_sec = int(by_diff.get(difficulty, by_diff.get("Medium", 90)))

    by_company = config.get("by_company") or {}
    if company_id and company_id in by_company:
        co = by_company[company_id]
        if co.get("prep_seconds") is not None:
            prep = int(co["prep_seconds"])
        if co.get("answer_seconds") is not None:
            answer_sec = int(co["answer_seconds"])
        if co.get("quiz_max_seconds") is not None:
            quiz_max = int(co["quiz_max_seconds"])

    return {
        "prep_seconds": prep,
        "answer_seconds": answer_sec,
        "quiz_max_seconds": quiz_max,
        "auto_next_on_timeout": config.get("auto_next_on_timeout", True),
        "show_ideal_after_submit_only": True,
        "difficulty": difficulty,
        "answer_by_difficulty": by_diff,
    }


@timer_bp.route("/settings", methods=["GET"])
def get_resolved_settings():
    db = get_db()
    company_id = request.args.get("company_id", "")
    difficulty = request.args.get("difficulty", "Medium")
    return jsonify(resolve_settings(db, company_id, difficulty))


@timer_bp.route("/settings/admin", methods=["GET"])
@admin_required
def get_admin_settings():
    db = get_db()
    config = _get_config_doc(db)
    companies = [
        {"id": str(c["_id"]), "name": c.get("name", "")}
        for c in db.companies.find().sort("name", 1)
    ]
    return jsonify({
        "prep_seconds": config.get("prep_seconds", PREP_SECONDS),
        "quiz_max_seconds": config.get("quiz_max_seconds", QUIZ_MAX_SECONDS),
        "answer_by_difficulty": {**ANSWER_BY_DIFFICULTY, **config.get("by_difficulty", {})},
        "by_company": config.get("by_company", {}),
        "auto_next_on_timeout": config.get("auto_next_on_timeout", True),
        "companies": companies,
        "updated_at": config.get("updated_at"),
    })


@timer_bp.route("/settings/admin", methods=["PUT"])
@admin_required
def update_admin_settings():
    db = get_db()
    data = request.get_json() or {}
    update = {
        "type": "config",
        "prep_seconds": int(data.get("prep_seconds", PREP_SECONDS)),
        "quiz_max_seconds": int(data.get("quiz_max_seconds", QUIZ_MAX_SECONDS)),
        "by_difficulty": data.get("by_difficulty", {}),
        "by_company": data.get("by_company", {}),
        "auto_next_on_timeout": data.get("auto_next_on_timeout", True),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    db.timer_settings.update_one({"type": "config"}, {"$set": update}, upsert=True)
    return jsonify({"message": "Timer settings saved", "updated_at": update["updated_at"]})
