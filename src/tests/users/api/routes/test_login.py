from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from core.config import settings
from core.security import verify_password
from tests.factories.user import UserFactory
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string
from utils import generate_password_reset_token


def test_get_access_token(user_factory: UserFactory, client: TestClient) -> None:
    user = user_factory.create(password="password")
    login_data = {
        "username": user.email,
        "password": "password",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


def test_get_access_token_incorrect_password(
    user_factory: UserFactory, client: TestClient
) -> None:
    user = user_factory.create(password="password")
    login_data = {
        "username": user.email,
        "password": "incorrect",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400


def test_use_access_token(
    user_factory: UserFactory,
    client: TestClient,
) -> None:
    user = user_factory.create(password="password")
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


def test_recovery_password(
    user_factory: UserFactory,
    client: TestClient,
) -> None:
    user = user_factory.create(password="password")
    with (
        patch("core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("core.config.settings.SMTP_USER", "admin@example.com"),
        patch("core.config.settings.EMAILS_FROM_EMAIL", "app@lucidexis.com"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/password-recovery/{user.email}",
            headers=user_authentication_headers(
                client=client, email=user.email, password="password"
            ),
        )
        assert r.status_code == 200
        assert r.json() == {"message": "Password recovery email sent"}


def test_recovery_password_user_not_exits(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    email = "jVgQr@example.com"
    r = client.post(
        f"{settings.API_V1_STR}/password-recovery/{email}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404


def test_reset_password(
    user_factory: UserFactory, client: TestClient, db: Session
) -> None:
    email = random_email()
    new_password = random_lower_string()

    user = user_factory.create(email=email, password="password")
    token = generate_password_reset_token(email=email)
    headers = user_authentication_headers(
        client=client, email=email, password="password"
    )
    data = {"new_password": new_password, "token": token}

    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=headers,
        json=data,
    )

    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully"}

    db.refresh(user)
    assert verify_password(new_password, user.hashed_password)


def test_reset_password_invalid_token(
    user_factory: UserFactory,
    client: TestClient,
) -> None:
    user = user_factory.create(password="password")
    data = {"new_password": "changethis", "token": "invalid"}
    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=data,
    )
    response = r.json()

    assert "detail" in response
    assert r.status_code == 400
    assert response["detail"] == "Invalid token"
