from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request


def create_token(user_id: str, role: str, expires_delta: timedelta | None = None) -> str:
    if expires_delta is None:
        expires_delta = (
            current_app.config["JWT_ADMIN_TOKEN_EXPIRES"]
            if role == "admin"
            else current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
        )
    payload = {
        "sub": user_id,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def get_token_from_header() -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def token_required(roles: list[str] | None = None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_from_header()
            if not token:
                return jsonify({"error": "Authentication required"}), 401
            payload = decode_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            if roles and payload.get("role") not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            g.current_user = payload
            return f(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(f):
    return token_required(roles=["admin"])(f)
