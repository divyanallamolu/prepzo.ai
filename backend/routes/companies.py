from bson import ObjectId
from flask import Blueprint, jsonify, request

from extensions import get_db
from utils.jwt_utils import admin_required, token_required

companies_bp = Blueprint("companies", __name__, url_prefix="/api/companies")


def _company(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name", ""),
        "slug": doc.get("slug", ""),
        "logo": doc.get("logo", ""),
        "description": doc.get("description", ""),
        "trending": doc.get("trending", False),
        "question_count": doc.get("question_count", 0),
    }


@companies_bp.route("", methods=["GET"])
def list_companies():
    db = get_db()
    trending_only = request.args.get("trending") == "true"
    query = {"trending": True} if trending_only else {}
    companies = [_company(c) for c in db.companies.find(query).sort("name", 1)]
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
    return jsonify(_company(doc))


@companies_bp.route("", methods=["POST"])
@admin_required
def create_company():
    from utils.helpers import save_logo

    db = get_db()
    if request.content_type and "multipart/form-data" in request.content_type:
        name = (request.form.get("name") or "").strip()
        description = request.form.get("description", "")
        trending = request.form.get("trending", "false").lower() == "true"
        logo = save_logo(request.files.get("logo"))
    else:
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        description = data.get("description", "")
        trending = bool(data.get("trending", False))
        logo = data.get("logo", "")

    if not name:
        return jsonify({"error": "Company name required"}), 400

    slug = name.lower().replace(" ", "-")
    doc = {
        "name": name,
        "slug": slug,
        "logo": logo or "",
        "description": description,
        "trending": trending,
        "question_count": 0,
    }
    result = db.companies.insert_one(doc)
    return jsonify(_company({**doc, "_id": result.inserted_id})), 201


@companies_bp.route("/<company_id>", methods=["PUT"])
@admin_required
def update_company(company_id):
    from utils.helpers import save_logo

    db = get_db()
    try:
        oid = ObjectId(company_id)
    except Exception:
        return jsonify({"error": "Invalid company id"}), 400

    updates = {}
    if request.content_type and "multipart/form-data" in request.content_type:
        if request.form.get("name"):
            updates["name"] = request.form.get("name").strip()
            updates["slug"] = updates["name"].lower().replace(" ", "-")
        if "description" in request.form:
            updates["description"] = request.form.get("description")
        if "trending" in request.form:
            updates["trending"] = request.form.get("trending", "false").lower() == "true"
        logo = save_logo(request.files.get("logo"))
        if logo:
            updates["logo"] = logo
    else:
        data = request.get_json() or {}
        for key in ("name", "description", "logo", "trending"):
            if key in data:
                updates[key] = data[key]
        if "name" in updates:
            updates["slug"] = updates["name"].lower().replace(" ", "-")

    if not updates:
        return jsonify({"error": "No updates provided"}), 400

    db.companies.update_one({"_id": oid}, {"$set": updates})
    doc = db.companies.find_one({"_id": oid})
    return jsonify(_company(doc))


@companies_bp.route("/<company_id>", methods=["DELETE"])
@admin_required
def delete_company(company_id):
    db = get_db()
    try:
        oid = ObjectId(company_id)
    except Exception:
        return jsonify({"error": "Invalid company id"}), 400
    db.companies.delete_one({"_id": oid})
    db.questions.delete_many({"company_id": str(oid)})
    return jsonify({"message": "Company deleted"})
