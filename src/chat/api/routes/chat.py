import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from chat.api.schemas.message import ErrorResponse, MessagePublic, MessageResponse
from chat.domain.models.message import MessageRole
from chat.domain.services.message import (
    MessageException,
    create_message,
)
from chat.infractructure.openai_client import OpenAIClienException, OpenAIClient
from core.db import get_db
from users.deps import get_current_user

logger = logging.getLogger(__name__)

websocket_router = APIRouter(tags=["websocket"])

OPENAI_USER_NOT_CONFIGURED_ASSISTANT_MESSAGE = (
    "It looks like you haven't configured your OpenAI API key and URL yet. "
    "Please go to your profile settings and add your OpenAI API credentials to start chatting!"
)

OPENAI_CLIENT_EXCEPTION_ASSITANT_MESSAGE = (
    "Sorry, I'm having trouble connecting to the OpenAI service right now. "
    "Please try again later or check your OpenAI API configuration."
)


@websocket_router.websocket("/ws/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: str,
    token: str | None = None,
) -> None:
    await websocket.accept()
    try:
        if not token:
            await websocket.send_json(
                ErrorResponse(error="Authentication token required").model_dump(
                    mode="json"
                )
            )
            await websocket.close()
            return
        db_gen = get_db()
        session = next(db_gen)
        try:
            user = get_current_user(session=session, token=token)
            conversation_uuid = uuid.UUID(conversation_id)
            logger.info(
                f"WebSocket connection established for user {user.id} "
                f"in conversation {conversation_id}"
            )
            if not user.openai_api_key or not user.openai_api_url:
                await websocket.send_json(
                    MessageResponse(
                        message=MessagePublic(
                            id=uuid.uuid4(),
                            content=OPENAI_USER_NOT_CONFIGURED_ASSISTANT_MESSAGE,
                            role=MessageRole.ASSISTANT,
                            conversation_id=conversation_uuid,
                        )
                    ).model_dump(mode="json")
                )
            openai_client = OpenAIClient(
                api_key=user.openai_api_key,  # type: ignore
                base_url=user.openai_api_url,  # type: ignore
            )
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                logger.info(f"Received message: {message_data}")
                user_message = create_message(
                    session=session,
                    conversation_id=conversation_uuid,
                    content=message_data["content"],
                    role=MessageRole.USER,
                )
                await websocket.send_json(
                    MessageResponse(
                        message=MessagePublic(
                            id=user_message.id,
                            content=user_message.content,
                            role=user_message.role,
                            conversation_id=user_message.conversation_id,
                        )
                    ).model_dump(mode="json")
                )
                if not user.openai_api_key or not user.openai_api_url:
                    bot_content = OPENAI_USER_NOT_CONFIGURED_ASSISTANT_MESSAGE
                else:
                    try:
                        bot_content = await openai_client.create_chat_completion(
                            model=user.llm_model,  # type: ignore
                            messages=[user_message.content],
                        )
                    except OpenAIClienException as e:
                        logger.warning(f"OpenAI client error: {e}")
                        bot_content = OPENAI_CLIENT_EXCEPTION_ASSITANT_MESSAGE
                bot_message = create_message(
                    session=session,
                    conversation_id=conversation_uuid,
                    content=bot_content,
                    role=MessageRole.ASSISTANT,
                )
                await websocket.send_json(
                    MessageResponse(
                        message=MessagePublic(
                            id=bot_message.id,
                            content=bot_message.content,
                            role=bot_message.role,
                            conversation_id=bot_message.conversation_id,
                        )
                    ).model_dump(mode="json")
                )
        except MessageException as e:
            logger.error(f"Message error: {e}")
            await websocket.send_json(
                ErrorResponse(error=str(e)).model_dump(mode="json")
            )
        finally:
            session.close()
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
