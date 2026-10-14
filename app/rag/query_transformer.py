import re


def transform_query(question: str) -> str:
    """
    Convert a customer question into a simple
    retrieval-friendly query.

    Temporary deterministic version.
    Later we can replace this with an LLM-based
    query transformer.
    """

    if not question.strip():
        raise ValueError("Question cannot be empty")

    query = question.lower().strip()

    # Remove common conversational phrases
    phrases_to_remove = [
        "can i",
        "could i",
        "would i",
        "please",
        "i want to know",
        "i want to",
        "what can i do",
        "what should i do",
        "tell me",
        "is it possible",
    ]

    for phrase in phrases_to_remove:
        query = query.replace(phrase, "")

    # Remove unnecessary punctuation
    query = re.sub(r"[^\w\s]", " ", query)

    # Normalize whitespace
    query = re.sub(r"\s+", " ", query).strip()

    return query