"""Consistent JSON API responses."""
from flask import jsonify


def ok(data=None, status: int = 200):
    body = data if data is not None else {}
    if isinstance(body, dict):
        return jsonify(body), status
    return jsonify(body), status


def error(message: str, status: int = 400, **extra):
    payload = {"error": message, **extra}
    return jsonify(payload), status
