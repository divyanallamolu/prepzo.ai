"""MongoDB Atlas connection — production only (no mocks)."""
import logging
import os
import time
from urllib.parse import urlparse

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConfigurationError, PyMongoError

logger = logging.getLogger("prepzo.db")

_client: MongoClient | None = None
_db: Database | None = None
_connected: bool = False
_last_error: str | None = None
DEFAULT_DB_NAME = "prepzo"
MAX_RETRIES = 3
RETRY_DELAY_SEC = 1.5


class DatabaseUnavailableError(Exception):
    """Raised when MongoDB is not connected."""


def database_name_from_uri(uri: str) -> str:
    try:
        path = urlparse(uri).path.strip("/")
        if path:
            return path.split("/")[0] or DEFAULT_DB_NAME
    except Exception:
        pass
    return os.environ.get("MONGO_DB_NAME", DEFAULT_DB_NAME)


def init_db(uri: str) -> Database:
    """Connect to MongoDB Atlas with retries. Raises on failure."""
    global _client, _db, _connected, _last_error

    uri = (uri or "").strip()
    if not uri:
        _last_error = "MONGO_URI environment variable is not set"
        logger.error(_last_error)
        raise ConfigurationError(_last_error)

    if uri.startswith("mongodb+srv://"):
        try:
            import dns  # noqa: F401
        except ImportError as exc:
            raise ConfigurationError(
                "dnspython is required for mongodb+srv URIs. Install: pip install dnspython"
            ) from exc

    db_name = database_name_from_uri(uri)
    client_kwargs: dict = {
        "serverSelectionTimeoutMS": 15000,
        "connectTimeoutMS": 15000,
        "retryWrites": True,
    }
    try:
        import certifi

        client_kwargs["tlsCAFile"] = certifi.where()
    except ImportError:
        pass

    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _client = MongoClient(uri, **client_kwargs)
            _client.admin.command("ping")
            _db = _client[db_name]
            _db.command("ping")
            _connected = True
            _last_error = None
            logger.info("MongoDB Atlas connected (db=%s, attempt=%s)", db_name, attempt)
            return _db
        except (PyMongoError, ConfigurationError, OSError) as exc:
            last_exc = exc
            _last_error = str(exc)
            logger.warning("MongoDB connection attempt %s/%s failed: %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC)

    _connected = False
    _db = None
    _client = None
    raise DatabaseUnavailableError(_last_error or "MongoDB connection failed") from last_exc


def get_db() -> Database:
    if _db is None or not _connected:
        raise DatabaseUnavailableError(_last_error or "MongoDB is not connected")
    return _db


def is_connected() -> bool:
    return _connected and _db is not None


def get_last_error() -> str | None:
    return _last_error


def ping() -> tuple[bool, str]:
    try:
        get_db().command("ping")
        return True, "MongoDB Atlas connected"
    except Exception as exc:
        return False, str(exc)
