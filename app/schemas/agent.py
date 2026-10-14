
from pydantic import BaseModel, Field


class AgentQuestion(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    conversation_id: int | None = Field(
        default=None,
        gt=0,
    )


class AgentResponse(BaseModel):
    answer: str
    conversation_id: int
    tools_used: list[str] = Field(
        default_factory=list,
    )

