import pymupdf

from app.services.pdf_processing import clean_text, extract_pdf


def test_extract_pdf_preserves_pages_and_metadata(tmp_path):
    path = tmp_path / "paper.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "A Clear Research Paper Title")
    page.insert_text((72, 110), "Authors: Ada Researcher and Ben Scientist")
    page.insert_text((72, 160), "Abstract")
    page.insert_text((72, 180), "This study aims to examine a research problem using a new method.")
    page.insert_text((72, 220), "Introduction")
    page.insert_text((72, 240), "Published in 2024. The challenge remains difficult.")
    document.set_metadata({"title": "Verified Paper Title", "author": "Ada Researcher; Ben Scientist"})
    document.save(path)
    document.close()

    extracted = extract_pdf(path)

    assert extracted.title == "Verified Paper Title"
    assert extracted.authors == ["Ada Researcher", "Ben Scientist"]
    assert extracted.publication_year == 2024
    assert len(extracted.pages) == 1
    assert "research problem" in (extracted.abstract or "")


def test_clean_text_joins_hyphenated_line_breaks():
    assert clean_text("trans-\nformer  models\x00") == "transformer models"
