from sqlmodel import Session

from chat.domain.models.message import Conversation
from chat.domain.services.message import get_conversation_messages
from tests.factories.message import ConversationFactory, MessageFactory
from tests.factories.user import UserFactory
from users.domain.models.user import User


def test_get_conversation_messages(
    user_factory: UserFactory,
    conversation_factory: ConversationFactory,
    message_factory: MessageFactory,
    db: Session,
) -> None:
    user: User = user_factory.create()
    conversation: Conversation = conversation_factory.create(user=user)
    message1 = message_factory.create(conversation=conversation)
    message2 = message_factory.create(conversation=conversation)
    messages = get_conversation_messages(
        session=db, user_id=user.id, conversation_id=conversation.id
    )
    assert len(messages) == 2
    assert messages[0].id == message1.id
    assert messages[1].id == message2.id
