"""Environment validation (never exposes secret values)."""
import os


REQUIRED = ("MONGO_URI", "JWT_SECRET_KEY", "FLASK_SECRET_KEY")


def env_flags() -> dict[str, bool]:
    return {key: bool(os.environ.get(key, "").strip()) for key in REQUIRED}


def missing_env() -> list[str]:
    return [k for k in REQUIRED if not os.environ.get(k, "").strip()]
