from fastapi.testclient import TestClient

from tests.factories.message import ConversationFactory
from tests.factories.user import UserFactory
from tests.utils.user import user_authentication_headers


def test_start_conversation(client: TestClient, user_factory: UserFactory) -> None:
    user = user_factory.create()
    response = client.post(
        "/api/v1/chat/start",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation" in data
    assert "id" in data["conversation"]


def test_get_latest_conversation(
    client: TestClient,
    user_factory: UserFactory,
    conversation_factory: ConversationFactory,
) -> None:
    user = user_factory.create()
    conversation_factory.create(user=user)
    conversation = conversation_factory.create(user=user)
    response = client.get(
        "/api/v1/chat/latest",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation" in data
    assert data["conversation"]["id"] == str(conversation.id)
