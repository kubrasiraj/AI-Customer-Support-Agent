from pathlib import Path


def extract_text(file_path: str) -> str:
    """
    Read a text file and return its content.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    text = path.read_text(
        encoding="utf-8"
    )

    if not text.strip():
        raise ValueError(
            "Document is empty"
        )

    return text