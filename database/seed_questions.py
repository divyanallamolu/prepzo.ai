"""Seed questions from data/questions.json. Usage: python seed_questions.py [--force]"""
import json
import os
import sys

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(os.path.join(ROOT, "backend", ".env"))
load_dotenv(os.path.join(ROOT, ".env"))


def _db_from_uri(uri: str):
    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    from urllib.parse import urlparse
    name = urlparse(uri).path.strip("/").split("/")[0] or "prepzo"
    return client[name]


def main(force: bool = False):
    uri = os.environ.get("MONGO_URI", "").strip()
    if not uri:
        print("Set MONGO_URI")
        sys.exit(1)

    data_path = os.path.join(os.path.dirname(__file__), "data", "questions.json")
    if not os.path.isfile(data_path):
        print("Run: python generate_questions.py first")
        sys.exit(1)

    with open(data_path, encoding="utf-8") as f:
        questions = json.load(f).get("questions", [])

    db = _db_from_uri(uri)
    if db.questions.count_documents({}) > 0 and not force:
        print(f"Questions exist ({db.questions.count_documents({})}). Use --force.")
        return

    if force:
        db.questions.delete_many({})

    companies = {c["name"]: c for c in db.companies.find()}
    inserted = 0
    seen = set()

    for q in questions:
        name = q.get("company_name", "")
        company = companies.get(name)
        if not company:
            continue
        text = (q.get("question_text") or q.get("question", "")).strip()
        key = (name.lower(), text.lower())
        if key in seen:
            continue
        seen.add(key)
        cid = str(company["_id"])
        db.questions.insert_one({
            "company_id": cid,
            "company_name": name,
            "title": q.get("title", text[:80]),
            "difficulty": q.get("difficulty", "Medium"),
            "category": q.get("category", "Technical"),
            "question_text": text,
            "question": text,
            "expected_answer": q.get("expected_answer", q.get("answer", "")),
            "answer": q.get("expected_answer", q.get("answer", "")),
            "explanation": q.get("explanation", q.get("expected_answer", "")),
            "tips": q.get("tips", []),
            "tags": q.get("tags", []),
            "frequency": q.get("frequency", "Medium"),
            "estimated_time": q.get("estimated_time", 60),
            "year_asked": str(q.get("year_asked", "2024")),
            "key_points": q.get("key_points", q.get("tips", [])),
        })
        inserted += 1

    for name, company in companies.items():
        cnt = db.questions.count_documents({"company_id": str(company["_id"])})
        db.companies.update_one({"_id": company["_id"]}, {"$set": {"question_count": cnt}})

    print(f"Seeded {inserted} questions.")


if __name__ == "__main__":
    main("--force" in sys.argv)
