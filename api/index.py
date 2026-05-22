"""
Vercel serverless entry — exports Flask `app` for @vercel/python runtime.

Env (Vercel dashboard): MONGO_URI, JWT_SECRET_KEY, FLASK_SECRET_KEY
"""
import os
import sys
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")

for path in (BACKEND, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

os.chdir(BACKEND)

# Force backend package into serverless bundle
import routes.auth  # noqa: F401,E402
import routes.companies  # noqa: F401,E402
import routes.health  # noqa: F401,E402
import routes.questions  # noqa: F401,E402

from app import app  # noqa: E402  Flask instance from backend/app.py


def _path_from_environ(environ) -> str:
    """Resolve real /api/... path when Vercel rewrites to /api/index."""
    path = environ.get("PATH_INFO") or ""
    if path.startswith("/api/") and path not in ("/api/index", "/api/index.py"):
        return path

    for key in (
        "REQUEST_URI",
        "RAW_URI",
        "HTTP_X_VERCEL_URI",
        "HTTP_X_VERCEL_FORWARDED_URI",
        "HTTP_X_INVOCATION_PATH",
        "HTTP_X_FORWARDED_URI",
        "HTTP_X_ORIGINAL_URI",
    ):
        raw = environ.get(key) or ""
        if not raw:
            continue
        if raw.startswith("/"):
            parsed = urlparse(raw)
            if parsed.path.startswith("/api"):
                return parsed.path
        elif "/api/" in raw:
            parsed = urlparse(raw if "://" in raw else f"http://host{raw}")
            if parsed.path.startswith("/api"):
                return parsed.path

    qs = environ.get("QUERY_STRING") or ""
    for part in qs.split("&"):
        if part.startswith("path="):
            candidate = unquote(part.split("=", 1)[1])
            if candidate.startswith("/api"):
                return candidate

    if path in ("/api/index", "/api/index.py", "/api", ""):
        return "/api/health"
    return path


class VercelPathMiddleware:
    """Fix PATH_INFO so Flask blueprints (/api/auth/login, etc.) match on Vercel."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        resolved = _path_from_environ(environ)
        if resolved:
            environ["PATH_INFO"] = resolved
            environ["SCRIPT_NAME"] = ""
        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

# Alternate handlers some Vercel runtimes probe
handler = app
application = app
