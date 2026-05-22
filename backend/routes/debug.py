"""Safe deployment diagnostics — never exposes secret values."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify

from extensions import get_db_error, get_db_mode, ping_database
from utils.env_check import env_status, missing_required_env

debug_bp = Blueprint("debug", __name__, url_prefix="/api/debug")


@debug_bp.route("/env", methods=["GET"])
def debug_env():
    db_ok, db_message = ping_database()
    missing = missing_required_env()

    return jsonify({
        "status": "ok" if not missing else "degraded",
        "service": "prepzo-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment_variables": env_status(),
        "missing_required": missing,
        "mongodb": {
            "connected": db_ok,
            "mode": get_db_mode(),
            "message": db_message,
            "last_error": get_db_error() if get_db_mode() != "mongodb" else None,
        },
        "hints": {
            "MONGO_URI": "Use mongodb+srv://... with database name, e.g. .../prepzo?retryWrites=true",
            "dnspython": "Required for mongodb+srv — listed in api/requirements.txt",
        },
    })
