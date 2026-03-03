import logging
import uuid

from fastapi import APIRouter

from chat.api.schemas.message import (
    MessagePublic,
    MessagesPublic,
)
from chat.domain.services.message import (
    get_conversation_messages,
)
from core.db import SessionDep
from users.deps import CurrentUser

logger = logging.getLogger(__name__)


conversation_router = APIRouter(tags=["conversation"])


@conversation_router.get("/{conversation_id}/messages", response_model=MessagesPublic)
async def get_messages(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
) -> MessagesPublic:
    messages = get_conversation_messages(
        session=session, user_id=current_user.id, conversation_id=conversation_id
    )
    return MessagesPublic(
        messages=[
            MessagePublic(
                id=message.id,
                content=message.content,
                role=message.role,
                conversation_id=message.conversation_id,
                additional_data=message.additional_data,
            )
            for message in messages
        ]
    )
