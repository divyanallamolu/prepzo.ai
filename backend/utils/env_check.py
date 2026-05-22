"""Environment and database status helpers (no secret values exposed)."""
import os
import traceback
from typing import Any

REQUIRED_VARS = ("MONGO_URI", "JWT_SECRET_KEY", "FLASK_SECRET_KEY")
OPTIONAL_VARS = ("ADMIN_EMAIL", "ADMIN_PASSWORD")


def env_status() -> dict[str, Any]:
    """Return which env vars are set (boolean only, never values)."""
    return {
        "MONGO_URI": bool((os.environ.get("MONGO_URI") or "").strip()),
        "JWT_SECRET_KEY": bool((os.environ.get("JWT_SECRET_KEY") or "").strip()),
        "FLASK_SECRET_KEY": bool((os.environ.get("FLASK_SECRET_KEY") or "").strip()),
        "ADMIN_EMAIL": bool((os.environ.get("ADMIN_EMAIL") or "").strip()),
        "ADMIN_PASSWORD": bool((os.environ.get("ADMIN_PASSWORD") or "").strip()),
    }


def missing_required_env() -> list[str]:
    status = env_status()
    return [k for k in REQUIRED_VARS if not status.get(k)]


def log_startup_diagnostics(logger) -> None:
    """Log MongoDB + env status at app startup."""
    from extensions import get_db_mode

    status = env_status()
    missing = missing_required_env()

    logger.info("Prepzo API running successfully on Vercel")
    logger.info("MongoDB connection mode: %s", get_db_mode())
    logger.info(
        "Environment variables present: MONGO_URI=%s JWT_SECRET_KEY=%s FLASK_SECRET_KEY=%s",
        status["MONGO_URI"],
        status["JWT_SECRET_KEY"],
        status["FLASK_SECRET_KEY"],
    )
    if missing:
        logger.warning("Missing required environment variables: %s", ", ".join(missing))
    else:
        logger.info("All required environment variables are set")


def format_exception(exc: BaseException) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
