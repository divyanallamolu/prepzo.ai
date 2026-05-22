"""Auto-seed MongoDB when collections are empty (production-safe, once per deploy)."""
import json
import logging
import os
import sys

import bcrypt
from bson import ObjectId
from datetime import datetime, timezone

logger = logging.getLogger("prepzo.seed")

_SEEDED_FLAG = False


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ensure_seeded(db) -> None:
    global _SEEDED_FLAG
    if _SEEDED_FLAG:
        return
    if db.companies.count_documents({}) > 0:
        _SEEDED_FLAG = True
        return

    logger.info("Empty database detected — running one-time auto-seed")
    sys.path.insert(0, os.path.join(_project_root(), "database"))
    from companies_config import COMPANIES  # noqa: E402

    company_ids = {}
    for c in COMPANIES:
        doc = {**c, "question_count": 0}
        res = db.companies.insert_one(doc)
        company_ids[c["name"]] = str(res.inserted_id)

    if db.users.count_documents({"role": "admin"}) == 0:
        pwd = os.environ.get("ADMIN_PASSWORD", "Admin@Prepzo2026")
        email = os.environ.get("ADMIN_EMAIL", "admin@prepzo.ai")
        db.users.insert_one({
            "name": "Admin",
            "email": email,
            "password": bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode(),
            "role": "admin",
            "streak": 0,
            "longest_streak": 0,
            "last_practice": None,
            "xp": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    qpath = os.path.join(_project_root(), "database", "data", "questions.json")
    if os.path.isfile(qpath):
        with open(qpath, encoding="utf-8") as f:
            questions = json.load(f).get("questions", [])
        seen = set()
        for q in questions:
            name = q.get("company_name", "")
            cid = company_ids.get(name)
            if not cid:
                continue
            text = (q.get("question_text") or q.get("question", "")).strip()
            key = (name.lower(), text.lower())
            if key in seen:
                continue
            seen.add(key)
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
                "explanation": q.get("explanation", ""),
                "tips": q.get("tips", []),
                "tags": q.get("tags", []),
                "frequency": q.get("frequency", "Medium"),
                "estimated_time": q.get("estimated_time", 60),
                "year_asked": str(q.get("year_asked", "2024")),
                "key_points": q.get("key_points", []),
            })

    for name, cid in company_ids.items():
        cnt = db.questions.count_documents({"company_id": cid})
        db.companies.update_one({"_id": ObjectId(cid)}, {"$set": {"question_count": cnt}})

    _SEEDED_FLAG = True
    logger.info("Auto-seed complete: %s companies", len(company_ids))
