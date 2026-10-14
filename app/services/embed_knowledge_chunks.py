from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.services.embedding_service import generate_embedding


def embed_knowledge_chunks(
    db: Session,
    document_id: int,
) -> int:
    """
    Generate embeddings for all chunks
    belonging to a knowledge document.
    """

    chunks = (
        db.query(KnowledgeChunk)
        .filter(
            KnowledgeChunk.document_id == document_id
        )
        .order_by(
            KnowledgeChunk.chunk_index
        )
        .all()
    )

    if not chunks:
        raise ValueError(
            "No chunks found for this document"
        )

    processed_count = 0

    for chunk in chunks:

        # Generate embedding from chunk text.
        embedding = generate_embedding(
            chunk.content
        )

        # Store the vector in the database.
        chunk.embedding = embedding

        processed_count += 1

    db.commit()

    return processed_count