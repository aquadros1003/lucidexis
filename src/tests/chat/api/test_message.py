from fastapi.testclient import TestClient

from tests.factories.message import ConversationFactory, MessageFactory
from tests.factories.user import UserFactory
from tests.utils.user import user_authentication_headers


def test_get_conversation_messages(
    client: TestClient,
    user_factory: UserFactory,
    conversation_factory: ConversationFactory,
    message_factory: MessageFactory,
) -> None:
    user = user_factory.create()
    conversation = conversation_factory.create(user=user)
    message1 = message_factory.create(conversation=conversation)
    message2 = message_factory.create(conversation=conversation)
    response = client.get(
        f"/api/v1/chat/{conversation.id}/messages",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 2
    assert data["messages"][0]["id"] == str(message1.id)
    assert data["messages"][1]["id"] == str(message2.id)
