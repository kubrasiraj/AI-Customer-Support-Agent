import pytest

from app.rag.context_compressor import compress_context


def test_empty_results_return_empty_string():
    assert compress_context([]) == ""


def test_formats_chunk_content():
    result = compress_context([
        {"chunk_id": 7, "content": "  Refunds are reviewed.  "}
    ])

    assert result == "[Knowledge Chunk 7]\nRefunds are reviewed."


def test_skips_blank_chunks():
    result = compress_context([
        {"chunk_id": 1, "content": "   "},
        {"chunk_id": 2, "content": "Useful policy"},
    ])

    assert "Knowledge Chunk 1" not in result
    assert "Useful policy" in result


def test_respects_context_limit():
    result = compress_context(
        [{"chunk_id": 1, "content": "x" * 500}],
        max_chars=120,
    )

    assert len(result) <= 120


def test_does_not_add_content_after_limit_is_reached():
    result = compress_context(
        [
            {"chunk_id": 1, "content": "a" * 120},
            {"chunk_id": 2, "content": "second chunk"},
        ],
        max_chars=150,
    )

    assert "second chunk" not in result