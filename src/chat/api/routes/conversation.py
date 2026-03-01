import logging

from fastapi import APIRouter

from chat.api.schemas.conversation import (
    ConversationPublic,
    LatestConversationResponse,
    StartConversationResponse,
)
from chat.domain.services.conversation import (
    get_latest_conversation as get_latest_conversation_service,
)
from chat.domain.services.conversation import (
    start_conversation as start_conversation_service,
)
from core.db import SessionDep
from users.deps import CurrentUser

logger = logging.getLogger(__name__)


conversation_router = APIRouter(tags=["conversation"])


@conversation_router.get("/latest", response_model=LatestConversationResponse)
async def get_latest_conversation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> LatestConversationResponse:
    conversation = get_latest_conversation_service(
        session=session, user_id=current_user.id
    )
    if not conversation:
        return LatestConversationResponse(conversation=None)
    return LatestConversationResponse(
        conversation=ConversationPublic.model_validate(conversation)
    )


@conversation_router.post("/start", response_model=StartConversationResponse)
async def start_conversation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> StartConversationResponse:
    conversation = start_conversation_service(session=session, user_id=current_user.id)
    return StartConversationResponse(
        conversation=ConversationPublic.model_validate(conversation)
    )
