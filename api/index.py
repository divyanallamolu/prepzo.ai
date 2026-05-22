"""Vercel legacy path — re-exports root Flask app from wsgi.py."""
from wsgi import app, application, handler  # noqa: F401
