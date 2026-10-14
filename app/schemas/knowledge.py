from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeDocumentResponse(BaseModel):
    id: int
    title: str
    file_name: str
    file_path: str
    category: str
    description: str | None
    version: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }