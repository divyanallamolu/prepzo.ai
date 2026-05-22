"""
Vercel / production WSGI entry at project root (bundles backend + ml).

Dashboard env: MONGO_URI, JWT_SECRET_KEY, FLASK_SECRET_KEY
"""
import os
import sys
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")

for path in (BACKEND, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

os.chdir(BACKEND)

from app import app  # noqa: E402  Flask application


def _path_from_environ(environ) -> str:
    path = environ.get("PATH_INFO") or ""
    if path.startswith("/api/") and path not in ("/api/index", "/api/index.py", "/wsgi.py"):
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

    if path in ("/api/index", "/api/index.py", "/wsgi.py", "/api", ""):
        return "/api/health"
    return path


class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        resolved = _path_from_environ(environ)
        if resolved:
            environ["PATH_INFO"] = resolved
            environ["SCRIPT_NAME"] = ""
        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
handler = app
application = app
