import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.memory.faiss_store import FAISSStore  # noqa: E402
from app.memory.embeddings import embed_text  # noqa: E402


@pytest.fixture
def store(tmp_path):
    return FAISSStore(str(tmp_path / "test_faiss"))


def test_add_and_search(store):
    store.add("reset my password", {"user_id": 1, "task_id": 1, "status": "pending"})
    results = store.search("I forgot my password")
    assert len(results) >= 1
    assert results[0]["score"] > 0.5


def test_find_duplicates_above_threshold(store):
    store.add("reset my password please", {"user_id": 1, "task_id": 1, "status": "pending"})
    duplicates = store.find_duplicates("I need to reset my password", threshold=0.7)
    assert len(duplicates) >= 1
    assert duplicates[0]["score"] >= 0.7


def test_no_duplicates_for_different_intent(store):
    store.add("reset my password", {"user_id": 1, "task_id": 1, "status": "pending"})
    duplicates = store.find_duplicates("what is the weather today", threshold=0.85)
    assert len(duplicates) == 0


def test_persist_and_reload(tmp_path):
    path = str(tmp_path / "persist_test")
    store1 = FAISSStore(path)
    store1.add("test persistence", {"user_id": 1, "task_id": 1, "status": "pending"})
    assert store1.total_vectors == 1

    store2 = FAISSStore(path)
    assert store2.total_vectors == 1
    results = store2.search("test persistence")
    assert len(results) == 1
    assert results[0]["score"] > 0.9


def test_empty_index_search(store):
    results = store.search("anything")
    assert results == []


def test_embed_text_returns_correct_dim():
    vec = embed_text("hello world")
    assert len(vec) == 384
