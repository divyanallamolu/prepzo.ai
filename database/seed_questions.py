"""
Seed MongoDB with 20+ interview questions per company (2024–2025).

Usage:
  cd database
  python seed_questions.py              # insert new questions only (skip duplicates)
  python seed_questions.py --reset      # delete all questions, re-seed counts
  python seed_questions.py --force      # insert even if questions exist (skip dupes)

Requires MongoDB (MONGO_URI in backend/.env) or run while Flask uses mongomock
(in-memory — data lost on restart).

Data source: data/interview_questions.json (generate via generate_question_bank.py)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

# Load env from backend
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/prepzo")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "data", "interview_questions.json")

sys.path.insert(0, SCRIPT_DIR)
from companies_config import COMPANIES  # noqa: E402


def normalize_question_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def load_questions_json():
    if not os.path.isfile(DATA_FILE):
        print(f"Missing {DATA_FILE}")
        print("Run: python generate_question_bank.py")
        sys.exit(1)
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    questions = data.get("questions") or data
    if not isinstance(questions, list):
        raise ValueError("JSON must contain a 'questions' array")
    return questions


def ensure_companies(db):
    """Create or update all companies; return name -> id map."""
    company_ids = {}
    for c in COMPANIES:
        existing = db.companies.find_one({"slug": c["slug"]})
        if existing:
            db.companies.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "name": c["name"],
                    "description": c["description"],
                    "trending": c.get("trending", False),
                }},
            )
            company_ids[c["name"]] = str(existing["_id"])
        else:
            doc = {
                "name": c["name"],
                "slug": c["slug"],
                "description": c["description"],
                "trending": c.get("trending", False),
                "logo": "",
                "question_count": 0,
            }
            result = db.companies.insert_one(doc)
            company_ids[c["name"]] = str(result.inserted_id)
            print(f"  + Company: {c['name']}")
    return company_ids


def recalc_question_counts(db):
    """Sync question_count on each company document."""
    for company in db.companies.find():
        cid = str(company["_id"])
        count = db.questions.count_documents({"company_id": cid})
        db.companies.update_one({"_id": company["_id"]}, {"$set": {"question_count": count}})


def is_duplicate(db, company_id: str, question: str) -> bool:
    normalized = question.strip()
    return db.questions.find_one({
        "company_id": company_id,
        "question": {"$regex": f"^{re.escape(normalized)}$", "$options": "i"},
    }) is not None


def seed(reset: bool = False, force: bool = False):
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.get_default_database()

    try:
        client.admin.command("ping")
        print(f"Connected to MongoDB: {MONGO_URI}")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        print("Start MongoDB locally or set MONGO_URI to MongoDB Atlas.")
        sys.exit(1)

    questions_data = load_questions_json()
    print(f"Loaded {len(questions_data)} questions from JSON")

    if reset:
        deleted = db.questions.delete_many({})
        print(f"Deleted {deleted.deleted_count} existing questions")
        db.companies.update_many({}, {"$set": {"question_count": 0}})

    existing_count = db.questions.count_documents({})
    if existing_count > 0 and not force and not reset:
        print(f"Database already has {existing_count} questions.")
        print("Use --force to add missing questions, or --reset to replace all.")

    print("Ensuring companies...")
    company_ids = ensure_companies(db)

    inserted = 0
    skipped_dup = 0
    skipped_missing_company = 0
    seen_global = set()

    for i, q in enumerate(questions_data, start=1):
        company_name = (q.get("company_name") or "").strip()
        question_text = (q.get("question") or "").strip()
        answer = (q.get("answer") or "").strip()

        if not company_name or not question_text or not answer:
            continue

        company_id = company_ids.get(company_name)
        if not company_id:
            skipped_missing_company += 1
            continue

        gkey = (company_name.lower(), normalize_question_text(question_text))
        if gkey in seen_global:
            skipped_dup += 1
            continue
        seen_global.add(gkey)

        if is_duplicate(db, company_id, question_text):
            skipped_dup += 1
            continue

        explanation = (q.get("explanation") or "").strip() or answer
        doc = {
            "company_id": company_id,
            "company_name": company_name,
            "question": question_text,
            "answer": answer,
            "explanation": explanation,
            "year_asked": q.get("year_asked") or "2024",
            "difficulty": q.get("difficulty") or "Medium",
            "category": q.get("category") or "Technical",
            "tags": q.get("tags") or [],
            "tips": q.get("tips") or [],
            "key_points": q.get("key_points") or [],
            "seeded_at": datetime.now(timezone.utc).isoformat(),
        }

        db.questions.insert_one(doc)
        inserted += 1

    recalc_question_counts(db)

    print("\n--- Seed summary ---")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped (duplicate): {skipped_dup}")
    print(f"  Skipped (unknown company): {skipped_missing_company}")

    print("\n  Questions per company:")
    for c in COMPANIES:
        cid = company_ids.get(c["name"])
        if cid:
            n = db.questions.count_documents({"company_id": cid})
            status = "OK" if n >= 20 else "LOW"
            print(f"    [{status}] {c['name']}: {n}")

    total = db.questions.count_documents({})
    print(f"\n  Total questions in DB: {total}")
    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Prepzo interview questions")
    parser.add_argument("--reset", action="store_true", help="Delete all questions first")
    parser.add_argument("--force", action="store_true", help="Run even if questions exist")
    args = parser.parse_args()
    seed(reset=args.reset, force=args.force)
