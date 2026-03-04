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
from chat.infractructure.messages import (
    OPENAI_CLIENT_EXCEPTION_ASSITANT_MESSAGE,
    OPENAI_USER_NOT_CONFIGURED_ASSISTANT_MESSAGE,
    SYSTEM_PROMPT,
)
from chat.infractructure.openai_client import OpenAIClienException, OpenAIClient
from core.config import settings
from core.db import get_db
from documents.domain.services.document import get_document_predictions
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
            if not user.openai_api_key or not user.openai_api_url or not user.llm_model:
                await websocket.send_json(
                    MessageResponse(
                        message=MessagePublic(
                            id=uuid.uuid4(),
                            content=OPENAI_USER_NOT_CONFIGURED_ASSISTANT_MESSAGE.get(
                                user.locale,
                                OPENAI_USER_NOT_CONFIGURED_ASSISTANT_MESSAGE["pl_PL"],
                            ),
                            role=MessageRole.ASSISTANT,
                            conversation_id=conversation_uuid,
                        )
                    ).model_dump(mode="json")
                )
            openai_client = OpenAIClient(
                api_key=user.openai_api_key,
                base_url=user.openai_api_url,
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
                    bot_content = OPENAI_USER_NOT_CONFIGURED_ASSISTANT_MESSAGE.get(
                        user.locale,
                        OPENAI_USER_NOT_CONFIGURED_ASSISTANT_MESSAGE["pl_PL"],
                    )
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
                try:
                    document_predictions = get_document_predictions(
                        embedding_model=websocket.app.state.embedding_model,
                        session=session,
                        owner_id=user.id,
                        search_query=user_message.content,
                    )
                    system_prompt = SYSTEM_PROMPT.get(
                        user.locale, SYSTEM_PROMPT["pl_PL"]
                    )
                    bot_content = await openai_client.create_chat_completion(
                        model=user.llm_model,  # type: ignore
                        messages=[user_message.content],
                        user_system_prompt=user.openai_system_prompt,
                        system_prompt=system_prompt
                        % (
                            user.locale,
                            "\n".join(
                                [
                                    f"- **{doc.filename}** (Category: {category}, Size: {doc.file_size} bytes)"
                                    for doc, category, _ in document_predictions
                                ]
                            ),
                        ),
                    )
                    bot_message = create_message(
                        session=session,
                        conversation_id=conversation_uuid,
                        content=bot_content,
                        role=MessageRole.ASSISTANT,
                        additional_data={
                            "files": [
                                {
                                    "id": str(doc.id),
                                    "filename": doc.filename,
                                    "file_size": doc.file_size,
                                    "content_type": doc.content_type,
                                    "download_url": f"{settings.BACKEND_HOST}/api/v1/documents/download/{doc.id}",
                                }
                                for doc, _, _ in document_predictions
                            ]
                        },
                    )
                    await websocket.send_json(
                        MessageResponse(
                            message=MessagePublic(
                                id=bot_message.id,
                                content=bot_message.content,
                                role=bot_message.role,
                                conversation_id=bot_message.conversation_id,
                                additional_data=bot_message.additional_data,
                            )
                        ).model_dump(mode="json")
                    )
                except OpenAIClienException as e:
                    logger.warning(f"OpenAI client error: {e}")
                    bot_content = OPENAI_CLIENT_EXCEPTION_ASSITANT_MESSAGE.get(
                        user.locale, OPENAI_CLIENT_EXCEPTION_ASSITANT_MESSAGE["en_US"]
                    )
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
