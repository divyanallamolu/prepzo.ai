"""
Vercel serverless entry — exposes the Flask app for all /api/* routes.

Vercel Root Directory: project root (Perpzo.ai folder — where vercel.json lives)
Static files: served from frontend/ (outputDirectory in vercel.json)

Set these env vars in Vercel Dashboard → Settings → Environment Variables:
  MONGO_URI, JWT_SECRET_KEY, FLASK_SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD
"""
import os
import sys

# Project paths for imports
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
VENDOR = os.path.join(os.path.dirname(__file__), "_vendor")

for path in (ROOT, BACKEND, VENDOR):
    if path not in sys.path:
        sys.path.insert(0, path)

os.chdir(BACKEND)

from app import app  # noqa: E402 — Flask application from backend/app.py


# Vercel Python runtime looks for `app` (WSGI)
# All HTTP methods route here via vercel.json rewrites
