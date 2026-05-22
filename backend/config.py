"""Application configuration from environment variables."""
import os
from datetime import timedelta

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _env(key: str, default: str = "") -> str:
    return (os.environ.get(key) or default).strip()


class Config:
    SECRET_KEY = _env("FLASK_SECRET_KEY")
    JWT_SECRET_KEY = _env("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ADMIN_TOKEN_EXPIRES = timedelta(hours=8)
    MONGO_URI = _env("MONGO_URI")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads", "logos")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}

    @classmethod
    def validate(cls) -> list[str]:
        missing = []
        if not cls.MONGO_URI:
            missing.append("MONGO_URI")
        if not cls.JWT_SECRET_KEY:
            missing.append("JWT_SECRET_KEY")
        if not cls.SECRET_KEY:
            missing.append("FLASK_SECRET_KEY")
        return missing
