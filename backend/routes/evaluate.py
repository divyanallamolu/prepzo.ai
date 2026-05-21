import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Blueprint, g, jsonify, request

from utils.jwt_utils import token_required

evaluate_bp = Blueprint("evaluate", __name__, url_prefix="/api/evaluate")


@evaluate_bp.route("", methods=["POST"])
@token_required()
def evaluate_answer():
    data = request.get_json() or {}
    user_answer = data.get("user_answer", "")
    ideal_answer = data.get("ideal_answer", "")
    question = data.get("question", "")

    if not user_answer or not ideal_answer:
        return jsonify({"error": "user_answer and ideal_answer required"}), 400

    try:
        from ml.evaluator import evaluate_response
        result = evaluate_response(user_answer, ideal_answer, question)
    except Exception as e:
        result = {
            "similarity_score": 0,
            "communication_score": 0,
            "keywords_matched": [],
            "keywords_missing": [],
            "suggestions": ["Could not run ML evaluation. Practice structuring your answer with STAR method."],
            "overall_score": 0,
            "feedback": str(e),
        }

    return jsonify(result)
