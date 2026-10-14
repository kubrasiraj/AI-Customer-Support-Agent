import pytest

from app.services.knowledge_service import split_text_into_chunks


def test_empty_text_returns_no_chunks():
    assert split_text_into_chunks("   ") == []


def test_short_text_returns_one_chunk():
    result = split_text_into_chunks(
        "Refund requests must follow company policy.",
        chunk_size=20,
        chunk_overlap=3,
    )

    assert len(result) == 1
    assert "Refund requests" in result[0]


def test_long_text_is_split_into_multiple_chunks():
    text = " ".join(f"word{i}" for i in range(25))

    result = split_text_into_chunks(
        text,
        chunk_size=10,
        chunk_overlap=2,
    )

    assert len(result) > 1
    assert all(chunk.strip() for chunk in result)


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        split_text_into_chunks(
            "Some sample text",
            chunk_size=5,
            chunk_overlap=5,
        )


def test_invalid_overlap_larger_than_chunk_size():
    with pytest.raises(ValueError):
        split_text_into_chunks(
            "Some sample text",
            chunk_size=5,
            chunk_overlap=6,
        )