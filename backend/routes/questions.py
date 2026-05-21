import json
import re

from bson import ObjectId
from flask import Blueprint, Response, jsonify, request

from extensions import get_db
from utils.bulk_import import parse_csv_text, parse_json_payload
from utils.jwt_utils import admin_required

questions_bp = Blueprint("questions", __name__, url_prefix="/api/questions")


def _question(doc: dict, include_answer: bool = True) -> dict:
    q = {
        "id": str(doc["_id"]),
        "company_id": doc.get("company_id", ""),
        "company_name": doc.get("company_name", ""),
        "question": doc.get("question", ""),
        "category": doc.get("category", "Technical"),
        "difficulty": doc.get("difficulty", "Medium"),
        "year_asked": doc.get("year_asked", ""),
        "tags": doc.get("tags", []),
        "tips": doc.get("tips", []),
        "key_points": doc.get("key_points", []),
    }
    if include_answer:
        q["answer"] = doc.get("answer", "")
        q["explanation"] = doc.get("explanation", "")
    return q


@questions_bp.route("", methods=["GET"])
def list_questions():
    db = get_db()
    company_id = request.args.get("company_id")
    category = request.args.get("category")
    difficulty = request.args.get("difficulty")
    query = {}
    if company_id:
        query["company_id"] = company_id
    if category:
        query["category"] = category
    if difficulty:
        query["difficulty"] = difficulty

    include_answer = request.args.get("preview") != "true"
    questions = [_question(q, include_answer=include_answer) for q in db.questions.find(query)]
    return jsonify(questions)


@questions_bp.route("/<question_id>", methods=["GET"])
def get_question(question_id):
    db = get_db()
    try:
        doc = db.questions.find_one({"_id": ObjectId(question_id)})
    except Exception:
        return jsonify({"error": "Invalid question id"}), 400
    if not doc:
        return jsonify({"error": "Question not found"}), 404
    return jsonify(_question(doc))


@questions_bp.route("", methods=["POST"])
@admin_required
def create_question():
    db = get_db()
    data = request.get_json() or {}
    required = ["company_id", "company_name", "question", "answer", "explanation"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": "Missing required fields"}), 400

    doc = {
        "company_id": data["company_id"],
        "company_name": data["company_name"],
        "question": data["question"],
        "answer": data["answer"],
        "explanation": data["explanation"],
        "year_asked": data.get("year_asked", ""),
        "difficulty": data.get("difficulty", "Medium"),
        "category": data.get("category", "Technical"),
        "tags": data.get("tags", []),
        "tips": data.get("tips", []),
        "key_points": data.get("key_points", []),
    }
    result = db.questions.insert_one(doc)
    db.companies.update_one(
        {"_id": ObjectId(data["company_id"])},
        {"$inc": {"question_count": 1}},
    )
    return jsonify(_question({**doc, "_id": result.inserted_id})), 201


@questions_bp.route("/<question_id>", methods=["PUT"])
@admin_required
def update_question(question_id):
    db = get_db()
    try:
        oid = ObjectId(question_id)
    except Exception:
        return jsonify({"error": "Invalid question id"}), 400

    data = request.get_json() or {}
    allowed = {
        "company_id", "company_name", "question", "answer", "explanation",
        "year_asked", "difficulty", "category", "tags", "tips", "key_points",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"error": "No updates provided"}), 400

    db.questions.update_one({"_id": oid}, {"$set": updates})
    doc = db.questions.find_one({"_id": oid})
    return jsonify(_question(doc))


@questions_bp.route("/<question_id>", methods=["DELETE"])
@admin_required
def delete_question(question_id):
    db = get_db()
    try:
        oid = ObjectId(question_id)
    except Exception:
        return jsonify({"error": "Invalid question id"}), 400

    doc = db.questions.find_one({"_id": oid})
    if doc:
        try:
            db.companies.update_one(
                {"_id": ObjectId(doc["company_id"])},
                {"$inc": {"question_count": -1}},
            )
        except Exception:
            pass
    db.questions.delete_one({"_id": oid})
    return jsonify({"message": "Question deleted"})


def _find_company_by_name(db, name: str):
    escaped = re.escape(name.strip())
    return db.companies.find_one({"name": {"$regex": f"^{escaped}$", "$options": "i"}})


def _is_duplicate(db, company_id: str, question: str) -> bool:
    normalized = question.strip().lower()
    existing = db.questions.find_one({
        "company_id": company_id,
        "question": {"$regex": f"^{re.escape(question.strip())}$", "$options": "i"},
    })
    return existing is not None


@questions_bp.route("/bulk", methods=["POST"])
@admin_required
def bulk_upload_questions():
    db = get_db()
    rows = []

    if request.is_json:
        rows = parse_json_payload(request.get_json())
    elif request.files.get("file"):
        upload = request.files["file"]
        filename = (upload.filename or "").lower()
        raw = upload.read().decode("utf-8-sig", errors="replace")
        if filename.endswith(".json"):
            rows = parse_json_payload(json.loads(raw))
        else:
            rows = parse_csv_text(raw)
    else:
        return jsonify({"error": "Upload a CSV/JSON file or send JSON body"}), 400

    if not rows:
        return jsonify({"error": "No valid questions found in upload"}), 400

    inserted = 0
    skipped_duplicates = 0
    skipped_errors = []

    for i, row in enumerate(rows, start=1):
        company = _find_company_by_name(db, row["company_name"])
        if not company:
            skipped_errors.append(f"Row {i}: company '{row['company_name']}' not found")
            continue

        company_id = str(company["_id"])
        if _is_duplicate(db, company_id, row["question"]):
            skipped_duplicates += 1
            continue

        doc = {
            "company_id": company_id,
            "company_name": company["name"],
            "question": row["question"],
            "answer": row["answer"],
            "explanation": row.get("explanation") or row["answer"],
            "year_asked": row.get("year_asked", ""),
            "difficulty": row.get("difficulty", "Medium"),
            "category": row.get("category", "Technical"),
            "tags": row.get("tags", []),
            "tips": [],
            "key_points": [],
        }
        db.questions.insert_one(doc)
        db.companies.update_one({"_id": company["_id"]}, {"$inc": {"question_count": 1}})
        inserted += 1

    return jsonify({
        "message": f"Imported {inserted} question(s)",
        "inserted": inserted,
        "skipped_duplicates": skipped_duplicates,
        "errors": skipped_errors,
        "total_rows": len(rows),
    }), 201


@questions_bp.route("/bulk/template", methods=["GET"])
@admin_required
def bulk_template():
    csv_content = (
        "company_name,difficulty,category,question,answer,explanation\n"
        'Google,Easy,Technical,"What is OOP?","Object Oriented Programming is a paradigm...","Explain classes and objects."\n'
        'Amazon,Medium,Behavioral,"Tell me about yourself","Use a concise professional summary...","Keep it under 2 minutes."\n'
    )
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=prepzo-questions-template.csv"},
    )


@questions_bp.route("/daily", methods=["GET"])
def daily_challenge():
    db = get_db()
    pipeline = [{"$sample": {"size": 1}}]
    result = list(db.questions.aggregate(pipeline))
    if not result:
        return jsonify({"error": "No questions available"}), 404
    return jsonify(_question(result[0], include_answer=False))
