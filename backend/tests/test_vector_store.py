import numpy as np

from app.core.config import settings
from app.services import vector_store


def test_persistent_vector_search_and_remove(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "vector_index_directory", tmp_path)
    monkeypatch.setattr(settings, "embedding_model_name", "unit-test-model")
    owner_id = "8b6d31bf-7d44-4a78-905d-5a273d343db8"
    chunk_ids = ["a6c2d145-34a1-4091-866f-34c9442b6a70", "fd46a671-0037-4812-bbd8-2a7c13dc820d"]
    vectors = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    vector_store.replace_paper(owner_id, [], chunk_ids, vectors)

    matches = vector_store.search(owner_id, np.array([0.9, 0.1], dtype=np.float32), limit=2)

    assert matches[0][0] == chunk_ids[0]
    assert matches[0][1] > matches[1][1]
    assert vector_store.has_index(owner_id)

    vector_store.remove_vectors(owner_id, chunk_ids[:1])
    remaining = vector_store.search(owner_id, np.array([0.9, 0.1], dtype=np.float32), limit=2)
    assert [chunk_id for chunk_id, _score in remaining] == [chunk_ids[1]]
