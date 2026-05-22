"""
Vercel serverless entry — Flask WSGI app for all /api/* routes.

Set env vars in Vercel: MONGO_URI, JWT_SECRET_KEY, FLASK_SECRET_KEY
Optional: ADMIN_EMAIL, ADMIN_PASSWORD
"""
import os
import sys
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
VENDOR = os.path.join(os.path.dirname(__file__), "vendor")

for path in (VENDOR, ROOT, BACKEND):
    if path not in sys.path and os.path.isdir(path):
        sys.path.insert(0, path)

os.chdir(BACKEND)

from app import create_app  # noqa: E402

_flask = create_app()


def _extract_api_path(environ) -> str:
    """Resolve the real /api/... path from Vercel serverless environ."""
    candidates = [
        environ.get("PATH_INFO", ""),
        environ.get("RAW_URI", ""),
        environ.get("REQUEST_URI", ""),
        environ.get("HTTP_X_VERCEL_INVOCATION_PATH", ""),
        environ.get("HTTP_X_INVOCATION_PATH", ""),
    ]
    for raw in candidates:
        if not raw:
            continue
        path = unquote(urlparse(raw).path if "://" in raw or raw.startswith("/") else raw.split("?")[0])
        if path.startswith("/api"):
            return path
    return environ.get("PATH_INFO", "") or "/api"


def _fix_path_info(environ):
    path = environ.get("PATH_INFO", "") or ""
    if path in ("/api/index", "/api/index.py", "/api", "/"):
        api_path = _extract_api_path(environ)
        if api_path.startswith("/api"):
            environ["PATH_INFO"] = api_path
            return
    if not path.startswith("/api"):
        api_path = _extract_api_path(environ)
        if api_path.startswith("/api"):
            environ["PATH_INFO"] = api_path


def application(environ, start_response):
    _fix_path_info(environ)
    return _flask.wsgi_app(environ, start_response)


app = application
handler = application
