from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.services.document_parser import extract_text


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    """
    Split text into smaller overlapping chunks.
    """

    if not text.strip():
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk_words = words[start:end]

        chunk = " ".join(chunk_words).strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - chunk_overlap

    return chunks


def process_knowledge_document(
    db: Session,
    document: KnowledgeDocument,
) -> int:
    """
    Extract text from a knowledge document,
    split it into chunks, and save the chunks
    in the database.
    """

    # Mark document as processing.
    document.status = "processing"
    db.commit()

    try:
        # Extract the original document text.
        text = extract_text(document.file_path)

        # Split document into smaller chunks.
        chunks = split_text_into_chunks(text)

        if not chunks:
            raise ValueError(
                "No text could be extracted from the document"
            )

        # Remove old chunks if the document is being reprocessed.
        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == document.id
        ).delete(
            synchronize_session=False
        )

        # Save each chunk.
        for index, content in enumerate(chunks):
            chunk = KnowledgeChunk(
                document_id=document.id,
                chunk_index=index,
                content=content,
            )

            db.add(chunk)

        # Mark document as successfully processed.
        document.status = "processed"

        db.commit()

        return len(chunks)

    except Exception:
        # Mark document as failed if anything goes wrong.
        db.rollback()

        document.status = "failed"
        db.commit()

        raise

