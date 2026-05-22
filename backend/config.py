import os
from datetime import timedelta

# Load .env locally; Vercel injects vars via os.environ directly
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _get_env(key: str, default: str = "") -> str:
    return (os.environ.get(key) or default).strip()


class Config:
    SECRET_KEY = _get_env("FLASK_SECRET_KEY", "prepzo-dev-secret-change-in-production")
    JWT_SECRET_KEY = _get_env("JWT_SECRET_KEY", "prepzo-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ADMIN_TOKEN_EXPIRES = timedelta(hours=8)
    MONGO_URI = _get_env("MONGO_URI", "mongodb://localhost:27017/prepzo")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads", "logos")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}

    @classmethod
    def validate_production(cls) -> list[str]:
        missing = []
        if not _get_env("MONGO_URI"):
            missing.append("MONGO_URI")
        if not _get_env("JWT_SECRET_KEY") or cls.JWT_SECRET_KEY.startswith("prepzo-jwt-secret"):
            if not _get_env("JWT_SECRET_KEY"):
                missing.append("JWT_SECRET_KEY")
        if not _get_env("FLASK_SECRET_KEY") or cls.SECRET_KEY.startswith("prepzo-dev-secret"):
            if not _get_env("FLASK_SECRET_KEY"):
                missing.append("FLASK_SECRET_KEY")
        return missing
