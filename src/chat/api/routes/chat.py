import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from chat.api.schemas.message import ErrorResponse, MessagePublic, MessageResponse
from chat.domain.models.message import MessageRole
from chat.domain.services.message import (
    MessageException,
    create_message,
    generate_bot_response,
)
from core.db import get_db
from users.deps import get_current_user

logger = logging.getLogger(__name__)

websocket_router = APIRouter(tags=["websocket"])


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
                bot_content = generate_bot_response(user_message.content)
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
        except Exception as e:
            logger.error(f"Error in WebSocket: {e}")
            await websocket.send_json(
                ErrorResponse(error="Internal server error").model_dump(mode="json")
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
