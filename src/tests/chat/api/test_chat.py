from fastapi.testclient import TestClient

from tests.factories.message import ConversationFactory
from tests.factories.user import UserFactory


def test_websocket_chat(
    client: TestClient,
    user_factory: UserFactory,
    conversation_factory: ConversationFactory,
) -> None:
    user = user_factory.create()
    conversation = conversation_factory.create(user=user)
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": user.email, "password": "password"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    with client.websocket_connect(
        f"/api/v1/chat/ws/{conversation.id}?token={token}"
    ) as websocket:
        websocket.send_json({"content": "Hello, bot!"})
        user_message_response = websocket.receive_json()
        assert user_message_response["type"] == "message"
        assert user_message_response["message"]["content"] == "Hello, bot!"
        assert user_message_response["message"]["role"] == "user"

        bot_message_response = websocket.receive_json()
        assert bot_message_response["type"] == "message"
        assert bot_message_response["message"]["role"] == "assistant"
        assert len(bot_message_response["message"]["content"]) > 0
