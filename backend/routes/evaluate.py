"""
POST /api/evaluate — AI answer scoring (calls ml/evaluator.py)

Request JSON:
  user_answer, ideal_answer, question (optional), category (optional)

Requires user JWT token.
"""
import os
import sys

# Ensure project root is on path so `ml` package imports work
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from flask import Blueprint, jsonify, request

from utils.jwt_utils import token_required

evaluate_bp = Blueprint("evaluate", __name__, url_prefix="/api/evaluate")


@evaluate_bp.route("", methods=["POST"])
@token_required()
def evaluate_answer():
    data = request.get_json() or {}
    user_answer = (data.get("user_answer") or "").strip()
    ideal_answer = (data.get("ideal_answer") or "").strip()
    question = data.get("question", "")
    category = data.get("category", "")

    if not user_answer or not ideal_answer:
        return jsonify({"error": "user_answer and ideal_answer required"}), 400

    try:
        from ml.evaluator import evaluate_response

        result = evaluate_response(user_answer, ideal_answer, question, category)
    except Exception as e:
        result = {
            "similarity_score": 0,
            "communication_score": 0,
            "overall_score": 0,
            "keywords_matched": [],
            "keywords_missing": [],
            "weak_areas": ["Evaluation unavailable"],
            "suggestions": [
                "Could not run evaluation. Structure your answer using the STAR method."
            ],
            "feedback": f"Evaluation error: {e}",
        }

    return jsonify(result)
