from sqlalchemy.orm import Session

from app.services.semantic_search import semantic_search


def retrieve_relevant_chunks(
    db: Session,
    query: str,
    top_k: int = 3,
    min_score: float = 0.30,
) -> list[dict]:
    """
    Retrieve relevant knowledge chunks
    above the minimum similarity score.
    """

    results = semantic_search(
        db=db,
        query=query,
        top_k=top_k,
    )

    filtered_results = [
        result
        for result in results
        if result["score"] >= min_score
    ]

    return filtered_results