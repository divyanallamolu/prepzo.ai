import logging
import os
from urllib.parse import urlparse

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConfigurationError, PyMongoError

logger = logging.getLogger("prepzo.db")

_client: MongoClient | None = None
_db: Database | None = None
_db_mode: str = "unknown"
_db_error: str | None = None
DEFAULT_DB_NAME = "prepzo"


def _database_name_from_uri(uri: str) -> str:
    """Extract DB name from Mongo URI; default prepzo for Atlas URIs without path."""
    try:
        path = urlparse(uri).path.strip("/")
        if path:
            return path.split("/")[0] or DEFAULT_DB_NAME
    except Exception:
        pass
    return os.environ.get("MONGO_DB_NAME", DEFAULT_DB_NAME)


def init_db(uri: str) -> Database:
    global _client, _db, _db_mode, _db_error

    uri = (uri or "").strip()
    if not uri:
        _db_error = "MONGO_URI is empty"
        logger.warning("%s — using in-memory database", _db_error)
        return _init_memory_db()

    db_name = _database_name_from_uri(uri)
    is_srv = uri.startswith("mongodb+srv://")

    if is_srv:
        try:
            import dns  # noqa: F401 — required for mongodb+srv

            logger.info("dnspython available for mongodb+srv")
        except ImportError:
            _db_error = 'dnspython not installed (required for mongodb+srv://). pip install dnspython'
            logger.error(_db_error)
            return _init_memory_db()

    kwargs: dict = {"serverSelectionTimeoutMS": 10000, "connectTimeoutMS": 10000}
    try:
        import certifi

        kwargs["tlsCAFile"] = certifi.where()
    except ImportError:
        pass

    try:
        _client = MongoClient(uri, **kwargs)
        _client.admin.command("ping")
        _db = _client[db_name]
        _db.command("ping")
        _db_mode = "mongodb"
        _db_error = None
        logger.info("MongoDB connected (database=%s, srv=%s)", db_name, is_srv)
        return _db
    except (PyMongoError, ConfigurationError, OSError, Exception) as exc:
        _db_error = str(exc)
        logger.error("MongoDB connection failed: %s", _db_error)
        logger.error("MongoDB traceback:\n%s", format_exception(exc))
        return _init_memory_db()


def format_exception(exc: BaseException) -> str:
    import traceback

    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def _init_memory_db() -> Database:
    global _client, _db, _db_mode

    import mongomock

    _client = mongomock.MongoClient()
    _db = _client[DEFAULT_DB_NAME]
    _db_mode = "memory"
    logger.warning("Using in-memory database (data resets each serverless cold start)")
    return _db


def get_db() -> Database:
    if _db is None:
        uri = os.environ.get("MONGO_URI", "")
        return init_db(uri)
    return _db


def get_db_mode() -> str:
    return _db_mode


def get_db_error() -> str | None:
    return _db_error


def ping_database() -> tuple[bool, str]:
    """Return (ok, message) for health/debug."""
    try:
        db = get_db()
        db.command("ping")
        if _db_mode == "mongodb":
            return True, "MongoDB Atlas connected"
        return True, "In-memory database (MongoDB unavailable)"
    except Exception as exc:
        return False, str(exc)
