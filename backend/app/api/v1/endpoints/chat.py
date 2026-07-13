from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)


class ChatMessage(BaseModel):
    message: str
    specialization_id: str | None = None
    roadmap_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    source: str = "ai_service"


@router.post("/message", response_model=ChatResponse)
def send_message(
    obj_in: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stub endpoint — routes to AI service (owned by AI teammate).
    AI teammate will replace the body of this function with
    their service call. Do not modify the request/response schemas
    without coordinating with the AI teammate first.
    """
    logger.info(
        f"Chat message from {current_user.email}: {obj_in.message[:50]}"
    )

    # TODO: AI teammate replaces this stub with actual AI service call
    # from app.services.ai_service import get_ai_response
    # return get_ai_response(obj_in.message, obj_in.specialization_id)

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Chat service not yet available — AI teammate is implementing this",
    )