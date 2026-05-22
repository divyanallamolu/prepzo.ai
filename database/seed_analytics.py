"""Initialize analytics collection indexes and sample structure."""
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, "backend", ".env"))
load_dotenv(os.path.join(ROOT, ".env"))


def main():
    uri = os.environ.get("MONGO_URI", "").strip()
    if not uri:
        print("Set MONGO_URI")
        sys.exit(1)

    from urllib.parse import urlparse
    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    name = urlparse(uri).path.strip("/").split("/")[0] or "prepzo"
    db = client[name]

    db.analytics.create_index([("user_id", ASCENDING), ("date", ASCENDING)], unique=True)
    db.sessions.create_index([("user_id", ASCENDING), ("started_at", ASCENDING)])
    db.revisions.create_index([("user_id", ASCENDING), ("question_id", ASCENDING)])
    db.bookmarks.create_index([("user_id", ASCENDING), ("question_id", ASCENDING)], unique=True)
    db.progress.create_index([("user_id", ASCENDING), ("completed_at", ASCENDING)])

    print("Analytics, sessions, revisions indexes ensured.")
    print(f"Collections: analytics={db.analytics.count_documents({})}, sessions={db.sessions.count_documents({})}")


if __name__ == "__main__":
    main()
