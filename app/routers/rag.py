from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.rag import RAGQuestion, RAGResponse
from app.services.rag_service import answer_customer_question


router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


@router.post(
    "/ask",
    response_model=RAGResponse,
)
def ask_rag_question(
    data: RAGQuestion,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ask a question using the knowledge base.
    """

    return answer_customer_question(
        db=db,
        question=data.question,
    )