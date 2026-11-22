import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pymupdf


class PdfTextError(ValueError):
    pass


@dataclass
class ExtractedPdf:
    title: str | None
    authors: list[str] | None
    abstract: str | None
    publication_year: int | None
    pages: list[str]


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("\x00", " ").replace("\f", "\n")
    value = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", value)
    lines = [re.sub(r"[\t\xa0 ]+", " ", line).strip() for line in value.splitlines()]
    output: list[str] = []
    previous_blank = False
    for line in lines:
        blank = not line
        if blank and previous_blank:
            continue
        output.append(line)
        previous_blank = blank
    return "\n".join(output).strip()


def _metadata_value(metadata: dict, key: str) -> str | None:
    value = metadata.get(key)
    if not isinstance(value, str):
        return None
    value = clean_text(value)
    if not value or value.lower() in {"untitled", "unknown", "none"}:
        return None
    return value


def _title(metadata: dict, first_page: str) -> str | None:
    value = _metadata_value(metadata, "title")
    if value:
        return value[:500]
    for line in first_page.splitlines():
        candidate = line.strip()
        if 8 <= len(candidate) <= 250 and not re.fullmatch(r"\d+", candidate):
            if candidate.casefold() not in {"abstract", "introduction", "research article"}:
                return candidate[:500]
    return None


def _authors(metadata: dict) -> list[str] | None:
    value = _metadata_value(metadata, "author")
    if not value:
        return None
    authors = [part.strip() for part in re.split(r";|\s+and\s+|\n", value) if part.strip()]
    return authors or None


def _abstract(text: str) -> str | None:
    patterns = [
        re.compile(r"(?is)\babstract\b\s*[:\n.]\s*(.{40,12000}?)(?=\n\s*(?:keywords?|index terms|\d+\.?\s*introduction|introduction)\b)"),
        re.compile(r"(?is)\babstract\b\s*[:\n.]\s*(.{80,6000})"),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            value = clean_text(match.group(1))
            if value:
                return value[:6000]
    return None


def _publication_year(metadata: dict, first_page: str) -> int | None:
    value = " ".join(str(metadata.get(key, "")) for key in ("publicationDate", "subject", "keywords"))
    value += " " + first_page[:12000]
    match = re.search(
        r"(?:published|publication|accepted|received|copyright|\bc\b|©)[^\n]{0,100}?\b((?:19|20)\d{2})\b",
        value,
        flags=re.IGNORECASE,
    )
    return int(match.group(1)) if match else None


def extract_pdf(path: Path) -> ExtractedPdf:
    try:
        with pymupdf.open(path) as document:
            if document.needs_pass:
                raise PdfTextError("This PDF is password-protected and cannot be processed.")
            pages = [clean_text(page.get_text("text", sort=True)) for page in document]
            if not pages or not any(pages):
                raise PdfTextError("No selectable text was found. Scanned PDFs need OCR, which is not enabled yet.")
            metadata = document.metadata or {}
    except PdfTextError:
        raise
    except Exception as exc:
        raise PdfTextError("The PDF could not be opened or read.") from exc

    full_text = "\n\n".join(f"{text}" for text in pages if text)
    first_page = pages[0] if pages else ""
    return ExtractedPdf(
        title=_title(metadata, first_page),
        authors=_authors(metadata),
        abstract=_abstract(full_text),
        publication_year=_publication_year(metadata, first_page),
        pages=pages,
    )
