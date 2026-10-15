
from pathlib import Path

from pypdf import PdfReader


def extract_text(file_path: str) -> str:
    """
    Extract text from a supported TXT or PDF document.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = path.suffix.lower()

    if extension == ".txt":
        text = path.read_text(encoding="utf-8")

    elif extension == ".pdf":
        reader = PdfReader(str(path))
        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    else:
        raise ValueError(
            "Unsupported file type. Only .txt and .pdf are supported."
        )

    if not text.strip():
        raise ValueError(
            "No extractable text found in document"
        )

    return text
