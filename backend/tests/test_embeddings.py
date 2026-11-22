import numpy as np

from app.services import embeddings


class FakeSentenceTransformer:
    def encode(self, texts, **kwargs):
        assert kwargs["normalize_embeddings"] is True
        return np.array([[3.0, 4.0] for _ in texts], dtype=np.float32)


def test_embedding_adapter_returns_float32_vectors(monkeypatch):
    monkeypatch.setattr(embeddings, "_model", FakeSentenceTransformer())

    vectors = embeddings.encode_texts(["research question"])

    assert vectors.dtype == np.float32
    assert vectors.shape == (1, 2)
    assert np.allclose(vectors[0], [3.0, 4.0])
