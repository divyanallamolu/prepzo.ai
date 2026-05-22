from bson import ObjectId
from flask import Blueprint, jsonify, request

from extensions import get_db
from models.company import serialize_company
from utils.jwt_utils import admin_required

companies_bp = Blueprint("companies", __name__, url_prefix="/api/companies")


@companies_bp.route("", methods=["GET"])
def list_companies():
    db = get_db()
    query = {}
    if request.args.get("trending") == "true":
        query["trending"] = True
    if request.args.get("difficulty"):
        query["difficulty"] = request.args.get("difficulty")
    if request.args.get("category"):
        query["category"] = request.args.get("category")
    search = (request.args.get("search") or "").strip()
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}},
        ]
    sort = request.args.get("sort", "name")
    sort_key = "popularity_score" if sort == "popularity" else "name"
    companies = [
        serialize_company(c)
        for c in db.companies.find(query).sort(sort_key, -1 if sort == "popularity" else 1)
    ]
    return jsonify(companies)


@companies_bp.route("/<company_id>", methods=["GET"])
def get_company(company_id):
    db = get_db()
    try:
        doc = db.companies.find_one({"_id": ObjectId(company_id)})
    except Exception:
        return jsonify({"error": "Invalid company id"}), 400
    if not doc:
        return jsonify({"error": "Company not found"}), 404
    return jsonify(serialize_company(doc))


@companies_bp.route("", methods=["POST"])
@admin_required
def create_company():
    from utils.helpers import save_logo

    db = get_db()
    data = request.get_json(silent=True) or {}
    if request.content_type and "multipart" in request.content_type:
        name = (request.form.get("name") or "").strip()
        logo = save_logo(request.files.get("logo"))
        doc = {
            "name": name,
            "slug": name.lower().replace(" ", "-"),
            "logo": logo or "",
            "description": request.form.get("description", ""),
            "trending": request.form.get("trending", "false").lower() == "true",
            "difficulty": request.form.get("difficulty", "Medium"),
            "category": request.form.get("category", "Product"),
            "tags": [],
            "interview_count": 0,
            "question_count": 0,
            "estimated_salary": "",
            "preparation_time": "",
            "hiring_status": "Actively hiring",
            "popularity_score": 50,
        }
    else:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Company name required"}), 400
        doc = {
            "name": name,
            "slug": data.get("slug", name.lower().replace(" ", "-")),
            "logo": data.get("logo", ""),
            "description": data.get("description", ""),
            "trending": bool(data.get("trending", False)),
            "difficulty": data.get("difficulty", "Medium"),
            "category": data.get("category", "Product"),
            "tags": data.get("tags", []),
            "interview_count": data.get("interview_count", 0),
            "question_count": 0,
            "estimated_salary": data.get("estimated_salary", ""),
            "preparation_time": data.get("preparation_time", ""),
            "hiring_status": data.get("hiring_status", ""),
            "popularity_score": data.get("popularity_score", 50),
        }
    result = db.companies.insert_one(doc)
    return jsonify(serialize_company({**doc, "_id": result.inserted_id})), 201
