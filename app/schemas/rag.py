from pydantic import BaseModel, Field


class RAGQuestion(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


class RAGSource(BaseModel):
    chunk_id: int
    document_id: int
    semantic_score: float
    keyword_score: float
    hybrid_score: float
    rerank_score: float


class RAGResponse(BaseModel):
    answer: str
    sources: list[RAGSource]