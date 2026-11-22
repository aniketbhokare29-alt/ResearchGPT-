from dataclasses import dataclass

from app.core.config import settings
from app.services.pdf_processing import clean_text


@dataclass
class TextChunk:
    chunk_index: int
    start_page: int
    end_page: int
    text: str
    token_count: int


def chunk_pages(pages: list[str], size_words: int | None = None, overlap_words: int | None = None) -> list[TextChunk]:
    size = size_words or settings.chunk_size_words
    overlap = settings.chunk_overlap_words if overlap_words is None else overlap_words
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Chunk overlap must be nonnegative and smaller than chunk size.")

    words_with_pages = [
        (word, page_number)
        for page_number, page_text in enumerate(pages, start=1)
        for word in clean_text(page_text).split()
    ]
    stride = size - overlap
    chunks: list[TextChunk] = []
    for start in range(0, len(words_with_pages), stride):
        portion = words_with_pages[start : start + size]
        if not portion:
            break
        chunks.append(
            TextChunk(
                chunk_index=len(chunks),
                start_page=portion[0][1],
                end_page=portion[-1][1],
                text=" ".join(word for word, _page in portion),
                token_count=len(portion),
            )
        )
        if start + size >= len(words_with_pages):
            break
    return chunks
