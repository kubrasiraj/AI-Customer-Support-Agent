
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.agent import AgentQuestion, AgentResponse
from app.services.agent_service import run_support_agent


router = APIRouter(
    prefix="/agent",
    tags=["AI Support Agent"],
)


@router.post(
    "/ask",
    response_model=AgentResponse,
)
def ask_support_agent(
    data: AgentQuestion,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ask the AI support agent while preserving
    conversation history for the authenticated customer.
    """

    return run_support_agent(
        db=db,
        user_id=current_user.id,
        question=data.question,
        conversation_id=data.conversation_id,
    )

