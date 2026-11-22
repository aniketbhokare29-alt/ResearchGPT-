from app.services.chunking import chunk_pages


def test_chunking_keeps_overlap_and_page_ranges():
    chunks = chunk_pages(["one two three", "four five six"], size_words=4, overlap_words=1)

    assert len(chunks) == 2
    assert chunks[0].text == "one two three four"
    assert chunks[0].start_page == 1
    assert chunks[0].end_page == 2
    assert chunks[1].text == "four five six"
    assert chunks[1].start_page == 2
    assert chunks[1].end_page == 2


def test_chunking_rejects_invalid_overlap():
    try:
        chunk_pages(["some text"], size_words=4, overlap_words=4)
    except ValueError as error:
        assert "smaller than chunk size" in str(error)
    else:
        raise AssertionError("Invalid overlap should be rejected")
