"""Tests for conversation memory management."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.services.database import Database  # noqa: E402
from app.memory.conversation import ConversationMemory  # noqa: E402


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test_conv.db"))


@pytest.fixture
def memory(db):
    return ConversationMemory(db)


def test_add_message(memory, db):
    uid = db.create_user("convuser", "conv@test.com", "hash")
    memory.add_message(uid, "user", "Hello, I need help")
    history = memory.get_history(uid)
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello, I need help"


def test_multiple_messages(memory, db):
    uid = db.create_user("multi", "multi@test.com", "hash")
    memory.add_message(uid, "user", "First message")
    memory.add_message(uid, "assistant", "First response")
    memory.add_message(uid, "user", "Second message")
    history = memory.get_history(uid)
    assert len(history) == 3


def test_get_context_empty(memory, db):
    uid = db.create_user("empty", "empty@test.com", "hash")
    context = memory.get_context(uid)
    assert context["summary"] is None
    assert context["recent_messages"] == []
    assert context["total_messages"] == 0


def test_get_context_with_messages(memory, db):
    uid = db.create_user("ctx", "ctx@test.com", "hash")
    memory.add_message(uid, "user", "Help me reset password")
    memory.add_message(uid, "assistant", "Sure, I can help with that")
    context = memory.get_context(uid)
    assert context["total_messages"] == 2
    assert len(context["recent_messages"]) == 2


def test_user_isolation(memory, db):
    uid1 = db.create_user("user1", "u1@test.com", "hash")
    uid2 = db.create_user("user2", "u2@test.com", "hash")
    memory.add_message(uid1, "user", "User 1 message")
    memory.add_message(uid2, "user", "User 2 message")
    h1 = memory.get_history(uid1)
    h2 = memory.get_history(uid2)
    assert len(h1) == 1
    assert len(h2) == 1
    assert h1[0]["content"] == "User 1 message"
    assert h2[0]["content"] == "User 2 message"
