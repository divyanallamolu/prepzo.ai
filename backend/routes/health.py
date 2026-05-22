"""Health check for deployment monitoring."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify

from extensions import get_db, get_db_mode, ping_database
from utils.env_check import env_status, missing_required_env

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health():
    db = get_db()
    try:
        db.command("ping")
        db_ok = True
    except Exception:
        db_ok = get_db_mode() == "memory"

    mongo_ok, mongo_msg = ping_database()
    return jsonify({
        "status": "ok",
        "service": "prepzo-api",
        "database": get_db_mode(),
        "database_ok": db_ok and mongo_ok,
        "database_message": mongo_msg,
        "env_configured": env_status(),
        "missing_env": missing_required_env(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
