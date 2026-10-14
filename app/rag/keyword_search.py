from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk


def keyword_search(
    db: Session,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Find knowledge chunks using simple keyword matching.
    """

    if not query.strip():
        raise ValueError("Query cannot be empty")

    query_words = set(query.lower().split())

    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.embedding.isnot(None))
        .all()
    )

    results = []

    for chunk in chunks:
        content_words = set(chunk.content.lower().split())

        matched_words = query_words.intersection(content_words)

        if not matched_words:
            continue

        score = len(matched_words) / len(query_words)

        results.append(
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "keyword_score": score,
            }
        )

    results.sort(
        key=lambda item: item["keyword_score"],
        reverse=True,
    )

    return results[:top_k]