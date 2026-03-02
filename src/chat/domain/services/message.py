import logging
import uuid

from sqlmodel import Session

from chat.domain.models.message import Conversation, Message, MessageRole

logger = logging.getLogger(__name__)


class MessageException(Exception):
    pass


def get_conversation_messages(
    *,
    session: Session,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> list[Message]:
    conversation = session.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != user_id:
        raise MessageException(
            f"Conversation {conversation_id} not found for user {user_id}"
        )
    if not conversation:
        raise MessageException(f"Conversation {conversation_id} not found")
    return conversation.messages


def create_message(
    *,
    session: Session,
    conversation_id: uuid.UUID,
    content: str,
    role: MessageRole,
) -> Message:
    logger.info(f"Creating message in conversation {conversation_id}")
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise MessageException(f"Conversation {conversation_id} not found")
    db_message = Message(
        content=content,
        role=role,
        conversation_id=conversation_id,
    )
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    logger.info(f"Created message {db_message.id}")
    return db_message


def generate_bot_response(user_message: str) -> str:
    responses = [
        f"Rozumiem, że pytasz o: {user_message[:50]}...",
        "To bardzo interesujące pytanie! Daj mi chwilę na namysł.",
        "Z pewnością mogę Ci w tym pomóc. Pozwól, że wyjaśnię...",
        "Świetne pytanie! Oto co myślę na ten temat...",
    ]
    import random

    return random.choice(responses)
