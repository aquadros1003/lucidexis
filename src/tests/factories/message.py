import factory
from pytest_factoryboy import register

from chat.domain.models.message import Conversation, Message, MessageRole
from tests.factories.base import TypedSQLAFactory
from tests.factories.user import UserFactory


@register
class ConversationFactory(TypedSQLAFactory["Conversation"]):
    class Meta:
        model = Conversation

    user = factory.SubFactory(UserFactory)


@register
class MessageFactory(TypedSQLAFactory["Message"]):
    class Meta:
        model = Message

    content = factory.Faker("text")
    role = factory.Iterator(MessageRole)
    conversation = factory.SubFactory(ConversationFactory)
