from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker = None


def get_reranker() -> CrossEncoder:
    """
    Load the reranker model only when it is needed.
    """

    global _reranker

    if _reranker is None:
        _reranker = CrossEncoder(MODEL_NAME)

    return _reranker


def rerank_results(
    query: str,
    results: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """
    Re-rank retrieved documents using a cross-encoder.
    """

    if not query.strip():
        raise ValueError("Query cannot be empty")

    if not results:
        return []

    reranker = get_reranker()

    pairs = [
        (query, result["content"])
        for result in results
    ]

    scores = reranker.predict(pairs)

    reranked_results = []

    for result, score in zip(results, scores):
        updated_result = result.copy()

        updated_result["rerank_score"] = float(score)

        reranked_results.append(updated_result)

    reranked_results.sort(
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return reranked_results[:top_k]