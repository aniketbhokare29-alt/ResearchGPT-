import logging
import os
import tempfile
import threading
from pathlib import Path
from uuid import UUID

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)
_lock = threading.RLock()


def _paths(owner_id: UUID | str) -> tuple[Path, Path]:
    root = settings.vector_index_directory.resolve()
    user_dir = (root / str(owner_id)).resolve()
    if not user_dir.is_relative_to(root):
        raise ValueError("Invalid vector index path.")
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "vectors.npz", user_dir / "index.faiss"


def _read_state(path: Path) -> tuple[np.ndarray, list[str], str | None]:
    if not path.exists():
        return np.empty((0, 0), dtype=np.float32), [], None
    with np.load(path, allow_pickle=False) as stored:
        vectors = np.asarray(stored["vectors"], dtype=np.float32)
        ids = [str(item) for item in stored["ids"].tolist()]
        model_name = str(stored["model_name"].item()) if "model_name" in stored.files else None
    if vectors.ndim != 2 or vectors.shape[0] != len(ids):
        raise ValueError("Stored vector index is inconsistent.")
    return vectors, ids, model_name


def _write_state(path: Path, vectors: np.ndarray, ids: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Invalidate the derived FAISS file before replacing its canonical vectors.
    # A crash between these operations then falls back to the matching NumPy data.
    path.with_name("index.faiss").unlink(missing_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix="vectors-", suffix=".npz", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as temporary_file:
            np.savez_compressed(
                temporary_file,
                vectors=np.asarray(vectors, dtype=np.float32),
                ids=np.asarray(ids, dtype="U36"),
                model_name=np.asarray(settings.embedding_model_name, dtype="U255"),
            )
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _write_faiss(path: Path, vectors: np.ndarray) -> None:
    try:
        import faiss

        if vectors.shape[0] == 0:
            path.unlink(missing_ok=True)
            return
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(np.ascontiguousarray(vectors, dtype=np.float32))
        temporary = path.with_suffix(".faiss.tmp")
        try:
            faiss.write_index(index, str(temporary))
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    except ImportError:
        path.unlink(missing_ok=True)
    except Exception:
        logger.exception("FAISS index could not be written; NumPy vectors remain the durable source.")
        path.unlink(missing_ok=True)


def replace_paper(owner_id: UUID | str, old_ids: list[str], new_ids: list[str], vectors: np.ndarray) -> None:
    with _lock:
        vectors_path, faiss_path = _paths(owner_id)
        existing_vectors, existing_ids, existing_model = _read_state(vectors_path)
        if existing_ids and existing_model != settings.embedding_model_name:
            raise ValueError("The embedding model changed. Rebuild the library index before adding more papers.")
        if existing_ids:
            keep = [index for index, value in enumerate(existing_ids) if value not in set(old_ids)]
            existing_vectors = existing_vectors[keep]
            existing_ids = [existing_ids[index] for index in keep]
        new_vectors = np.asarray(vectors, dtype=np.float32)
        if len(new_ids) != new_vectors.shape[0]:
            raise ValueError("Embedding count does not match chunk count.")
        if existing_vectors.shape[0] and new_vectors.shape[0] and existing_vectors.shape[1] != new_vectors.shape[1]:
            raise ValueError("Embedding dimensions changed; rebuild this user's vector index.")
        if existing_vectors.shape[0] == 0:
            combined = new_vectors
        elif new_vectors.shape[0] == 0:
            combined = existing_vectors
        else:
            combined = np.concatenate((existing_vectors, new_vectors), axis=0)
        combined_ids = existing_ids + new_ids
        _write_state(vectors_path, combined, combined_ids)
        _write_faiss(faiss_path, combined)


def remove_vectors(owner_id: UUID | str, chunk_ids: list[str]) -> None:
    if not chunk_ids:
        return
    replace_paper(owner_id, chunk_ids, [], np.empty((0, 0), dtype=np.float32))


def search(owner_id: UUID | str, query_vector: np.ndarray, limit: int = 10) -> list[tuple[str, float]]:
    with _lock:
        vectors_path, faiss_path = _paths(owner_id)
        vectors, ids, model_name = _read_state(vectors_path)
        if not ids:
            return []
        if model_name != settings.embedding_model_name:
            raise ValueError("The embedding model changed. The library index must be rebuilt.")
        query = np.asarray(query_vector, dtype=np.float32).reshape(1, -1)
        if vectors.shape[1] != query.shape[1]:
            raise ValueError("Query and stored embedding dimensions differ.")
        try:
            import faiss

            if faiss_path.exists():
                index = faiss.read_index(str(faiss_path))
                if index.ntotal == len(ids) and index.d == vectors.shape[1]:
                    scores, positions = index.search(query, min(limit, len(ids)))
                    return [
                        (ids[int(position)], float(score))
                        for position, score in zip(positions[0], scores[0])
                        if position >= 0
                    ]
        except (ImportError, OSError, RuntimeError):
            pass
        scores = vectors @ query[0]
        positions = np.argsort(scores)[::-1][: min(limit, len(ids))]
        return [(ids[int(position)], float(scores[position])) for position in positions]


def has_index(owner_id: UUID | str) -> bool:
    return _paths(owner_id)[0].exists()


def rebuild_from_chunks(owner_id: UUID | str, chunks: list) -> None:
    """Rebuild durable vectors from persisted per-chunk embeddings when files are missing."""
    ids: list[str] = []
    rows: list[list[float]] = []
    stale_chunks = []
    for chunk in chunks:
        embedding = getattr(chunk, "embedding", None)
        ids.append(str(chunk.id))
        if not embedding or getattr(chunk, "embedding_model", None) != settings.embedding_model_name:
            stale_chunks.append(chunk)
            rows.append([])
        else:
            rows.append(embedding)
    if not ids:
        return
    if stale_chunks:
        from app.services.embeddings import encode_texts

        fresh = encode_texts([chunk.text for chunk in chunks])
        for chunk, vector in zip(chunks, fresh):
            chunk.embedding = vector.tolist()
            chunk.embedding_model = settings.embedding_model_name
            chunk.vector_id = str(chunk.id)
        rows = [vector.tolist() for vector in fresh]
    vectors = np.asarray(rows, dtype=np.float32)
    with _lock:
        vectors_path, faiss_path = _paths(owner_id)
        _write_state(vectors_path, vectors, ids)
        _write_faiss(faiss_path, vectors)
