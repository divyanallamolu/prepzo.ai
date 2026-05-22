"""
Vercel serverless Flask entry (project-root /api — required by Vercel).

Backend is bundled to api/_backend during build (see vercel.json buildCommand).
"""
import os
import sys
from urllib.parse import unquote, urlparse

API_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLED_BACKEND = os.path.join(API_DIR, "_backend")
REPO_BACKEND = os.path.abspath(os.path.join(API_DIR, "..", "backend"))
BACKEND = BUNDLED_BACKEND if os.path.isdir(BUNDLED_BACKEND) else REPO_BACKEND
DATABASE_DIR = os.path.join(API_DIR, "database")
REPO_DATABASE = os.path.abspath(os.path.join(API_DIR, "..", "database"))

for path in (BACKEND, API_DIR, DATABASE_DIR, REPO_DATABASE):
    if path and os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)

os.chdir(BACKEND)

from app import app  # noqa: E402

print("Prepzo API running successfully on Vercel", flush=True)


def _path_from_environ(environ) -> str:
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
