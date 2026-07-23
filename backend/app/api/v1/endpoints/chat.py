from uuid import UUID
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import get_current_user
from app.crud import crud_roadmap
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
    logger.info(
        f"Chat message from {current_user.email}: {obj_in.message[:50]}"
    )

    # Fetch roadmap nodes for context if roadmap_id provided
    nodes = []
    if obj_in.roadmap_id:
        try:
            roadmap = crud_roadmap.get(db, roadmap_id=UUID(obj_in.roadmap_id))
            if roadmap:
                nodes = roadmap.nodes or []
        except Exception:
            pass  # Invalid UUID or not found — proceed with empty context

    from app.services.ai_service import AIService
    ai = AIService()
    result = ai.chat_with_context(message=obj_in.message, nodes=nodes)

    logger.info(
        f"Chat response via {result['source']} "
        f"for {current_user.email}"
    )
    return ChatResponse(reply=result["reply"], source=result["source"])
