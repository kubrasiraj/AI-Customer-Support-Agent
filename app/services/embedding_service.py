from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def generate_embedding(text: str) -> list[float]:
    """
    Convert text into a numerical embedding vector.
    """

    if not text.strip():
        raise ValueError("Text cannot be empty")

    embedding = model.encode(
        text,
        normalize_embeddings=True,
    )

    return embedding.tolist()