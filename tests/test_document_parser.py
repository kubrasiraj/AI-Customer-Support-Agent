from pathlib import Path

import pytest

from app.services.document_parser import extract_text


def test_extracts_text_from_file(tmp_path: Path):
    file_path = tmp_path / "policy.txt"
    file_path.write_text("Refunds are subject to policy.", encoding="utf-8")

    result = extract_text(file_path)

    assert result == "Refunds are subject to policy."


def test_missing_file_raises_error(tmp_path: Path):
    file_path = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        extract_text(file_path)


def test_whitespace_only_file_raises_error(tmp_path: Path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("   \n  ", encoding="utf-8")

    with pytest.raises(ValueError):
        extract_text(file_path)


def test_preserves_meaningful_multiline_text(tmp_path: Path):
    file_path = tmp_path / "policy.txt"
    file_path.write_text(
        "Refund policy\nContact support for help.",
        encoding="utf-8",
    )

    result = extract_text(file_path)

    assert "Refund policy" in result
    assert "Contact support for help." in result