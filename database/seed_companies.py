"""Seed companies collection. Usage: python seed_companies.py [--force]"""
import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(os.path.join(ROOT, "backend", ".env"))
load_dotenv(os.path.join(ROOT, ".env"))

from companies_config import COMPANIES  # noqa: E402


def main(force: bool = False):
    uri = os.environ.get("MONGO_URI", "").strip()
    if not uri:
        print("Set MONGO_URI in environment or backend/.env")
        sys.exit(1)

    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    db = client.get_default_database() if "/" in uri.split("?")[0].rstrip("/")[-20:] else client["prepzo"]
    if db.name == "admin":
        db = client["prepzo"]

    if db.companies.count_documents({}) > 0 and not force:
        print(f"Companies already seeded ({db.companies.count_documents({})} docs). Use --force to replace.")
        return

    if force:
        db.companies.delete_many({})

    for c in COMPANIES:
        doc = {**c, "question_count": 0, "logo": c.get("logo", "")}
        db.companies.insert_one(doc)

    print(f"Seeded {len(COMPANIES)} companies.")


if __name__ == "__main__":
    main("--force" in sys.argv)
