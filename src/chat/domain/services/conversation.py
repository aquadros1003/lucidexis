import logging
import uuid

from sqlmodel import Session, col, select

from chat.domain.models.message import Conversation

logger = logging.getLogger(__name__)


class ConversationException(Exception):
    pass


def get_latest_conversation(
    *,
    session: Session,
    user_id: uuid.UUID,
) -> Conversation | None:
    return session.exec(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(col(Conversation.created_at).desc())
    ).first()


def start_conversation(
    *,
    session: Session,
    user_id: uuid.UUID,
) -> Conversation:
    logger.info(f"Starting conversation for {user_id=}")
    db_obj = Conversation(user_id=user_id)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    logger.info(f"Started conversation {db_obj.id} for {user_id=}")
    return db_obj
