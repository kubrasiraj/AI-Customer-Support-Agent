import math

from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.services.embedding_service import generate_embedding


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """
    Calculate cosine similarity between two vectors.
    """

    if len(vector_a) != len(vector_b):
        raise ValueError("Vectors must have the same dimensions")

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def semantic_search(
    db: Session,
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """
    Find the most relevant knowledge chunks
    for a user query.
    """

    if not query.strip():
        raise ValueError("Query cannot be empty")

    query_embedding = generate_embedding(query)

    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.embedding.isnot(None))
        .all()
    )

    results = []

    for chunk in chunks:
        similarity = cosine_similarity(
            query_embedding,
            chunk.embedding,
        )

        results.append(
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "score": similarity,
            }
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:top_k]