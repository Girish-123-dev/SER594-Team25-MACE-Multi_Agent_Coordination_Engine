import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.services.database import Database  # noqa: E402


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test.db"))


def test_create_user(db):
    uid = db.create_user("alice", "alice@example.com", "hash123")
    assert uid == 1


def test_get_user_by_username(db):
    db.create_user("bob", "bob@example.com", "hash123")
    user = db.get_user_by_username("bob")
    assert user["username"] == "bob"


def test_get_user_by_email(db):
    db.create_user("carol", "carol@example.com", "hash123")
    user = db.get_user_by_email("carol@example.com")
    assert user["email"] == "carol@example.com"


def test_get_user_by_id(db):
    uid = db.create_user("dave", "dave@example.com", "hash123")
    user = db.get_user_by_id(uid)
    assert user["username"] == "dave"


def test_create_task(db):
    uid = db.create_user("eve", "eve@example.com", "hash123")
    tid = db.create_task(uid, "reset password", "support")
    assert tid == 1


def test_get_tasks_by_user(db):
    uid = db.create_user("frank", "frank@example.com", "hash123")
    db.create_task(uid, "task1", "support")
    db.create_task(uid, "task2", "domain")
    tasks = db.get_tasks_by_user(uid)
    assert len(tasks) == 2
