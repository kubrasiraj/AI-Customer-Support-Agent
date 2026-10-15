
from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.services.document_parser import extract_text
from app.services.embed_knowledge_chunks import embed_knowledge_chunks


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    """Split text into smaller overlapping chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be non-negative and smaller than chunk_size"
        )

    if not text.strip():
        return []

    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end]).strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - chunk_overlap

    return chunks


def process_knowledge_document(
    db: Session,
    document: KnowledgeDocument,
) -> int:
    """Extract, chunk, embed, and process a knowledge document."""

    document.status = "processing"
    db.commit()

    try:
        text = extract_text(document.file_path)
        chunks = split_text_into_chunks(text)

        if not chunks:
            raise ValueError(
                "No text could be extracted from the document"
            )

        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == document.id
        ).delete(synchronize_session=False)

        for index, content in enumerate(chunks):
            db.add(
                KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=content,
                )
            )

        # Save chunks first so the embedding service can query them.
        db.commit()

        # Generate and save embeddings for the document's chunks.
        embed_knowledge_chunks(db, document.id)

        # Mark as processed only after embedding succeeds.
        document.status = "processed"
        db.commit()

        return len(chunks)

    except Exception:
        db.rollback()
        document.status = "failed"
        db.commit()
        raise
