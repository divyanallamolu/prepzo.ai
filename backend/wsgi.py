"""
Vercel serverless entry point.
Deploy: backend/wsgi.py via vercel.json @vercel/python build.
"""
import os
import sys
from urllib.parse import unquote, urlparse

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

for path in (PROJECT_ROOT, BACKEND_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

os.chdir(BACKEND_DIR)

from app import create_app  # noqa: E402

app = create_app()


def _resolve_path(environ) -> str:
    path = environ.get("PATH_INFO") or ""
    if path.startswith("/api/") and path not in ("/api/index", "/backend/wsgi.py", "/wsgi.py"):
        return path

    for key in ("REQUEST_URI", "RAW_URI", "HTTP_X_VERCEL_URI", "HTTP_X_FORWARDED_URI"):
        raw = environ.get(key) or ""
        if not raw:
            continue
        parsed = urlparse(raw if raw.startswith("/") else f"http://x{raw}")
        if parsed.path.startswith("/api"):
            return parsed.path

    qs = environ.get("QUERY_STRING") or ""
    for part in qs.split("&"):
        if part.startswith("path="):
            p = unquote(part.split("=", 1)[1])
            if p.startswith("/api"):
                return p
    return path


class _VercelPathFix:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        resolved = _resolve_path(environ)
        if resolved.startswith("/api"):
            environ["PATH_INFO"] = resolved
            environ["SCRIPT_NAME"] = ""
        return self.wsgi_app(environ, start_response)


app.wsgi_app = _VercelPathFix(app.wsgi_app)
handler = app
application = app

print("Prepzo API running successfully on Vercel", flush=True)
