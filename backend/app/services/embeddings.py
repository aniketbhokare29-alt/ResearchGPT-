import threading

import numpy as np

from app.core.config import settings

_load_lock = threading.Lock()
_model = None


def _get_model():
    global _model
    if _model is None:
        with _load_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                device = settings.model_device
                if device == "auto":
                    import torch

                    device = "cuda" if torch.cuda.is_available() else "cpu"
                _model = SentenceTransformer(settings.embedding_model_name, device=device)
    return _model


def encode_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype=np.float32)
    vectors = _get_model().encode(
        texts,
        batch_size=settings.embedding_batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return np.asarray(vectors, dtype=np.float32)
