"""Seed minimal data when using in-memory database."""

from datetime import datetime, timezone

import bcrypt

COMPANIES = [
    {"name": "Google", "slug": "google", "description": "Search, cloud, and AI leader", "trending": True},
    {"name": "Amazon", "slug": "amazon", "description": "E-commerce and AWS cloud giant", "trending": True},
    {"name": "Microsoft", "slug": "microsoft", "description": "Enterprise software and cloud", "trending": True},
    {"name": "Meta", "slug": "meta", "description": "Social media and metaverse", "trending": True},
    {"name": "Apple", "slug": "apple", "description": "Consumer hardware and services", "trending": True},
]


def seed_if_empty(db):
    if db.companies.count_documents({}) > 0:
        return

    for company in COMPANIES:
        db.companies.insert_one({**company, "logo": "", "question_count": 0})

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
