from sqlalchemy.orm import Session

from app.services.semantic_search import semantic_search
from app.rag.keyword_search import keyword_search


def hybrid_search(
    db: Session,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Combine semantic search and keyword search.

    Semantic search weight: 70%
    Keyword search weight: 30%
    """

    if not query.strip():
        raise ValueError("Query cannot be empty")

    semantic_results = semantic_search(
        db=db,
        query=query,
        top_k=top_k,
    )

    keyword_results = keyword_search(
        db=db,
        query=query,
        top_k=top_k,
    )

    combined = {}

    # Add semantic search results
    for result in semantic_results:
        chunk_id = result["chunk_id"]

        combined[chunk_id] = {
            "chunk_id": chunk_id,
            "document_id": result["document_id"],
            "chunk_index": result["chunk_index"],
            "content": result["content"],
            "semantic_score": result["score"],
            "keyword_score": 0.0,
        }

    # Add keyword search results
    for result in keyword_results:
        chunk_id = result["chunk_id"]

        if chunk_id not in combined:
            combined[chunk_id] = {
                "chunk_id": chunk_id,
                "document_id": result["document_id"],
                "chunk_index": result["chunk_index"],
                "content": result["content"],
                "semantic_score": 0.0,
                "keyword_score": result["keyword_score"],
            }
        else:
            combined[chunk_id]["keyword_score"] = result["keyword_score"]

    # Calculate hybrid score
    results = []

    for result in combined.values():
        hybrid_score = (
            0.70 * result["semantic_score"]
            + 0.30 * result["keyword_score"]
        )

        result["hybrid_score"] = hybrid_score

        results.append(result)

    # Highest hybrid score first
    results.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )

    return results[:top_k]