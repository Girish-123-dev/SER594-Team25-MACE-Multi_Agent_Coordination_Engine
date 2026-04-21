import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.services.database import Database, get_db
from app.main import app

_test_db = None


def _get_test_db() -> Database:
    global _test_db
    if _test_db is None:
        _test_db = Database(db_path=":memory:")
    return _test_db


app.dependency_overrides[get_db] = _get_test_db


def pytest_sessionfinish(session, exitstatus):
    global _test_db
    if _test_db is not None:
        _test_db.close()
        _test_db = None
    app.dependency_overrides.pop(get_db, None)
