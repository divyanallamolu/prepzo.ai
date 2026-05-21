import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "prepzo-dev-secret-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "prepzo-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ADMIN_TOKEN_EXPIRES = timedelta(hours=8)
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/prepzo")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads", "logos")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}
