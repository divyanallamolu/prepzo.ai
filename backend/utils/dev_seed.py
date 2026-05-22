"""Seed companies and questions when using in-memory database."""

import json
import os
import re
from datetime import datetime, timezone

import bcrypt

# Path to question bank JSON
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QUESTIONS_JSON = os.path.join(PROJECT_ROOT, "database", "data", "interview_questions.json")
COMPANIES_PY = os.path.join(PROJECT_ROOT, "database", "companies_config.py")


def _load_companies():
    import sys
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "database"))
    from companies_config import COMPANIES
    return COMPANIES


def _load_questions():
    if not os.path.isfile(QUESTIONS_JSON):
        return []
    with open(QUESTIONS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("questions") or []


def seed_if_empty(db):
    if db.companies.count_documents({}) > 0:
        return

    companies = _load_companies()
    company_ids = {}

    for company in companies:
        result = db.companies.insert_one({**company, "logo": "", "question_count": 0})
        company_ids[company["name"]] = str(result.inserted_id)

    if db.users.count_documents({"role": "admin"}) == 0:
        db.users.insert_one({
            "name": "Admin",
            "email": "admin@prepzo.ai",
            "password": bcrypt.hashpw(b"Admin@Prepzo2026", bcrypt.gensalt()).decode(),
            "role": "admin",
            "streak": 0,
            "last_practice": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    questions = _load_questions()
    seen = set()
    for q in questions:
        name = q.get("company_name", "")
        cid = company_ids.get(name)
        if not cid:
            continue
        text = (q.get("question") or "").strip()
        key = (name.lower(), text.lower())
        if key in seen:
            continue
        seen.add(key)
        db.questions.insert_one({
            "company_id": cid,
            "company_name": name,
            "question": text,
            "answer": q.get("answer", ""),
            "explanation": q.get("explanation") or q.get("answer", ""),
            "year_asked": q.get("year_asked", "2024"),
            "difficulty": q.get("difficulty", "Medium"),
            "category": q.get("category", "Technical"),
            "tags": q.get("tags", []),
            "tips": q.get("tips", []),
            "key_points": q.get("key_points", []),
        })

    for name, cid in company_ids.items():
        from bson import ObjectId
        count = db.questions.count_documents({"company_id": cid})
        db.companies.update_one({"_id": ObjectId(cid)}, {"$set": {"question_count": count}})

    if db.timer_settings.count_documents({}) == 0:
        google_id = company_ids.get("Google", "")
        amazon_id = company_ids.get("Amazon", "")
        db.timer_settings.insert_one({
            "type": "config",
            "defaults": {
                "thinking_seconds": 180,
                "interview_duration_seconds": 1200,
                "reveal_delay_seconds": 0,
                "auto_reveal": True,
            },
            "by_difficulty": {
                "Easy": {"thinking_seconds": 120},
                "Medium": {"thinking_seconds": 240},
                "Hard": {"thinking_seconds": 360},
            },
            "by_company": {
                **({google_id: {"thinking_seconds": 120, "interview_duration_seconds": 1200}} if google_id else {}),
                **({amazon_id: {"thinking_seconds": 180, "interview_duration_seconds": 1500}} if amazon_id else {}),
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
