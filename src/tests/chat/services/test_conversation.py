from sqlmodel import Session

from chat.domain.models.message import Conversation
from chat.domain.services.conversation import (
    get_latest_conversation,
    start_conversation,
)
from tests.factories.message import ConversationFactory
from tests.factories.user import UserFactory
from users.domain.models.user import User


def test_start_conversation(
    user_factory: UserFactory,
    db: Session,
) -> None:
    user: User = user_factory.create()
    conversation = start_conversation(session=db, user_id=user.id)
    assert conversation.user_id == user.id
    assert conversation in user.conversations


def test_start_conversation_with_existing_conversation(
    user_factory: UserFactory,
    conversation_factory: ConversationFactory,
    db: Session,
) -> None:
    user: User = user_factory.create()
    existing_conversation: Conversation = conversation_factory.create(user=user)
    new_conversation = start_conversation(session=db, user_id=user.id)
    assert new_conversation.user_id == user.id
    assert new_conversation in user.conversations
    assert existing_conversation in user.conversations


def test_get_latest_conversation(
    user_factory: UserFactory,
    conversation_factory: ConversationFactory,
    db: Session,
) -> None:
    user: User = user_factory.create()
    conversation_factory.create(user=user)
    conversation2: Conversation = conversation_factory.create(user=user)
    latest_conversation = get_latest_conversation(session=db, user_id=user.id)
    assert latest_conversation is not None
    assert latest_conversation.id == conversation2.id
