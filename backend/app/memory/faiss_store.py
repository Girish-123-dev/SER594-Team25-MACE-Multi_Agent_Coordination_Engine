import json
import logging
from pathlib import Path

import faiss
import numpy as np

from app.config import settings
from app.memory.embeddings import embed_text, EMBEDDING_DIM

logger = logging.getLogger(__name__)


class FAISSStore:
    def __init__(self, index_path: str | None = None):
        self.index_path = Path(index_path or settings.faiss_index_path)
        self.index_file = self.index_path / "intent_index.faiss"
        self.map_file = self.index_path / "intent_map.json"
        self.index_path.mkdir(parents=True, exist_ok=True)

        self.index: faiss.IndexFlatIP = self._load_or_create_index()
        self.id_map: dict[int, dict] = self._load_id_map()

    def _load_or_create_index(self) -> faiss.IndexFlatIP:
        if self.index_file.exists():
            logger.info("Loading FAISS index from %s", self.index_file)
            return faiss.read_index(str(self.index_file))
        logger.info("Creating new FAISS index (dim=%d)", EMBEDDING_DIM)
        return faiss.IndexFlatIP(EMBEDDING_DIM)

    def _load_id_map(self) -> dict[int, dict]:
        if self.map_file.exists():
            with open(self.map_file, "r") as f:
                raw = json.load(f)
            return {int(k): v for k, v in raw.items()}
        return {}

    def save(self):
        faiss.write_index(self.index, str(self.index_file))
        with open(self.map_file, "w") as f:
            json.dump(self.id_map, f, indent=2)
        logger.info("FAISS index saved (%d vectors)", self.index.ntotal)

    def add(self, text: str, metadata: dict) -> int:
        vector = np.array([embed_text(text)], dtype=np.float32)
        idx = self.index.ntotal
        self.index.add(vector)
        self.id_map[idx] = {"text": text, **metadata}
        self.save()
        return idx

    def search(self, text: str, top_k: int = 5) -> list[dict]:
        if self.index.ntotal == 0:
            return []
        vector = np.array([embed_text(text)], dtype=np.float32)
        scores, indices = self.index.search(vector, min(top_k, self.index.ntotal))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            entry = self.id_map.get(int(idx), {})
            results.append({"score": float(score), "index": int(idx), **entry})
        return results

    def find_duplicates(self, text: str, threshold: float | None = None) -> list[dict]:
        threshold = threshold or settings.similarity_threshold
        results = self.search(text, top_k=5)
        return [r for r in results if r["score"] >= threshold]

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal


_store: FAISSStore | None = None


def get_faiss_store() -> FAISSStore:
    global _store
    if _store is None:
        _store = FAISSStore()
    return _store
