"""
Timer settings API — global, per-company, and per-difficulty controls.

GET  /api/timer/settings?company_id=&difficulty=  — resolved settings (public)
GET  /api/timer/settings/admin                    — full config (admin)
PUT  /api/timer/settings/admin                    — update config (admin)
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from extensions import get_db
from utils.jwt_utils import admin_required

timer_bp = Blueprint("timer", __name__, url_prefix="/api/timer")

# Default values (seconds)
DEFAULT_CONFIG = {
    "defaults": {
        "thinking_seconds": 180,
        "interview_duration_seconds": 1200,
        "reveal_delay_seconds": 0,
        "auto_reveal": True,
    },
    "by_difficulty": {
        "Easy": {"thinking_seconds": 120},
        "Medium": {"thinking_seconds": 240},
        "Hard": {"thinking_seconds": 360},
    },
    "by_company": {},
}


def _get_config_doc(db):
    doc = db.timer_settings.find_one({"type": "config"})
    if not doc:
        doc = {"type": "config", **DEFAULT_CONFIG}
        db.timer_settings.insert_one({**doc, "updated_at": datetime.now(timezone.utc).isoformat()})
    return doc


def _merge_settings(base: dict, override: dict) -> dict:
    """Merge override into base (only known keys)."""
    keys = ("thinking_seconds", "interview_duration_seconds", "reveal_delay_seconds", "auto_reveal")
    out = dict(base)
    for k in keys:
        if k in override and override[k] is not None:
            out[k] = override[k]
    return out


def resolve_settings(db, company_id: str = "", difficulty: str = "") -> dict:
    """
    Priority: company override > difficulty (thinking only) > defaults.
    Returns effective timer config for the interview room.
    """
    config = _get_config_doc(db)
    defaults = {**DEFAULT_CONFIG["defaults"], **config.get("defaults", {})}

    resolved = {
        "thinking_seconds": int(defaults.get("thinking_seconds", 180)),
        "interview_duration_seconds": int(defaults.get("interview_duration_seconds", 1200)),
        "reveal_delay_seconds": int(defaults.get("reveal_delay_seconds", 0)),
        "auto_reveal": bool(defaults.get("auto_reveal", True)),
        "source": {"defaults": True},
    }

    # Difficulty override (thinking time)
    by_diff = config.get("by_difficulty") or DEFAULT_CONFIG["by_difficulty"]
    if difficulty and difficulty in by_diff:
        diff_cfg = by_diff[difficulty]
        if "thinking_seconds" in diff_cfg:
            resolved["thinking_seconds"] = int(diff_cfg["thinking_seconds"])
            resolved["source"]["difficulty"] = difficulty

    # Company override (all fields)
    by_company = config.get("by_company") or {}
    if company_id and company_id in by_company:
        company_cfg = by_company[company_id]
        resolved = _merge_settings(resolved, company_cfg)
        resolved["source"]["company_id"] = company_id
        # Fetch company name for display
        from bson import ObjectId
        try:
            c = db.companies.find_one({"_id": ObjectId(company_id)})
            if c:
                resolved["source"]["company_name"] = c.get("name", "")
        except Exception:
            pass

    return resolved


@timer_bp.route("/settings", methods=["GET"])
def get_resolved_settings():
    """Public: effective timer for a company + difficulty combination."""
    db = get_db()
    company_id = request.args.get("company_id", "")
    difficulty = request.args.get("difficulty", "")
    resolved = resolve_settings(db, company_id, difficulty)
    return jsonify(resolved)


@timer_bp.route("/settings/admin", methods=["GET"])
@admin_required
def get_admin_settings():
    """Admin: full timer configuration document."""
    db = get_db()
    config = _get_config_doc(db)
    companies = [
        {"id": str(c["_id"]), "name": c.get("name", "")}
        for c in db.companies.find().sort("name", 1)
    ]
    return jsonify({
        "defaults": {**DEFAULT_CONFIG["defaults"], **config.get("defaults", {})},
        "by_difficulty": {**DEFAULT_CONFIG["by_difficulty"], **config.get("by_difficulty", {})},
        "by_company": config.get("by_company", {}),
        "companies": companies,
        "updated_at": config.get("updated_at"),
    })


@timer_bp.route("/settings/admin", methods=["PUT"])
@admin_required
def update_admin_settings():
    """Admin: save timer configuration."""
    db = get_db()
    data = request.get_json() or {}

    update = {
        "type": "config",
        "defaults": data.get("defaults", DEFAULT_CONFIG["defaults"]),
        "by_difficulty": data.get("by_difficulty", {}),
        "by_company": data.get("by_company", {}),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    db.timer_settings.update_one({"type": "config"}, {"$set": update}, upsert=True)
    return jsonify({"message": "Timer settings saved", "updated_at": update["updated_at"]})
