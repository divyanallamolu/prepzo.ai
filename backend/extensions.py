from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

_client: MongoClient | None = None
_db: Database | None = None
_db_mode: str = "unknown"


def init_db(uri: str) -> Database:
    global _client, _db, _db_mode

    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        _client.admin.command("ping")
        _db = _client.get_default_database()
        _db_mode = "mongodb"
        return _db
    except (PyMongoError, OSError, Exception):
        import mongomock

        _client = mongomock.MongoClient()
        _db = _client["prepzo"]
        _db_mode = "memory"
        return _db


def get_db() -> Database:
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db


def get_db_mode() -> str:
    return _db_mode
