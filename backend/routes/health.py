"""Health check — deployment and monitoring."""
from datetime import datetime, timezone

from flask import Blueprint, jsonify

from extensions import get_last_error, is_connected, ping
from utils.env_check import env_flags, missing_env

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health():
    db_ok, db_msg = ping()
    missing = missing_env()
    return jsonify({
        "status": "ok" if db_ok and not missing else "degraded",
        "service": "prepzo-api",
        "mongodb_connected": db_ok and is_connected(),
        "database_message": db_msg,
        "database_error": get_last_error() if not db_ok else None,
        "environment": env_flags(),
        "missing_env": missing,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
