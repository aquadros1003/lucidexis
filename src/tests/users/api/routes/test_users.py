import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session, select

import users.domain.services.user as user_service
from core.config import settings
from core.security import verify_password
from tests.factories.user import UserFactory
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string
from users.domain.models.user import User as DbUser


def test_get_users_superuser_me(client: TestClient, user_factory: UserFactory) -> None:
    user = user_factory.create(is_superuser=True, password="password")
    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]


def test_get_users_normal_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False


def test_create_user_new_email(
    client: TestClient, db: Session, user_factory: UserFactory
) -> None:
    user = user_factory.create(password="password", is_superuser=True)
    with (
        patch("utils.send_email", return_value=None),
        patch("core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        email = random_email()
        password = random_lower_string()
        data = {"email": email, "password": password}
        r = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=user_authentication_headers(
                client=client, email=user.email, password="password"
            ),
            json=data,
        )
        assert 200 <= r.status_code < 300
        created_user = r.json()
        db_user = user_service.get_user_by_email(session=db, email=email)
        assert db_user
        assert db_user.email == created_user["email"]


def test_get_existing_user(
    client: TestClient, db: Session, user_factory: UserFactory
) -> None:
    user = user_factory.create(is_superuser=True, password="password")
    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = user_service.get_user_by_email(session=db, email=user.email)
    assert existing_user
    assert existing_user.email == api_user["email"]


def test_get_existing_user_current_user(client: TestClient, db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    user = user_service.create_user(session=db, email=username, password=password)
    user_id = user.id

    login_data = {
        "username": username,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    r = client.get(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=headers,
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = user_service.get_user_by_email(session=db, email=username)
    assert existing_user
    assert existing_user.email == api_user["email"]


def test_get_existing_user_permissions_error(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}


def test_create_user_existing_username(
    client: TestClient, user_factory: UserFactory
) -> None:
    user = user_factory.create(is_superuser=True, password="password")
    data = {"email": user.email, "password": "password"}
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=data,
    )
    created_user = r.json()
    assert r.status_code == 400
    assert "_id" not in created_user


def test_create_user_by_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password}
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 403


def test_retrieve_users(client: TestClient, user_factory: UserFactory) -> None:
    user_factory.create(password="password1")
    user_factory.create(password="password2")
    user = user_factory.create(password="password", is_superuser=True)

    r = client.get(
        f"{settings.API_V1_STR}/users/",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    all_users = r.json()

    assert len(all_users["data"]) > 1
    assert "count" in all_users
    for item in all_users["data"]:
        assert "email" in item


def test_update_user_me(
    client: TestClient, db: Session, user_factory: UserFactory
) -> None:
    user = user_factory.create(password="password")
    full_name = "Updated Name"
    email = random_email()
    data = {"full_name": full_name, "email": email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["email"] == email
    assert updated_user["full_name"] == full_name

    user_query = select(DbUser).where(DbUser.email == email)
    user_db = db.exec(user_query).first()
    db.refresh(user_db)
    assert user_db
    assert user_db.email == email
    assert user_db.full_name == full_name


def test_update_password_me(
    client: TestClient, db: Session, user_factory: UserFactory
) -> None:
    user = user_factory.create(password="password")
    new_password = random_lower_string()
    data = {
        "current_password": "password",
        "new_password": new_password,
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["message"] == "Password updated successfully"

    user_query = select(DbUser).where(DbUser.email == user.email)
    user_db = db.exec(user_query).first()
    db.refresh(user_db)
    assert user_db
    assert user_db.email == user.email
    assert verify_password(new_password, user_db.hashed_password)


def test_update_password_me_incorrect_password(
    client: TestClient, user_factory: UserFactory
) -> None:
    user = user_factory.create(password="password")
    new_password = random_lower_string()
    data = {"current_password": new_password, "new_password": new_password}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert updated_user["detail"] == "Incorrect password"


def test_update_user_me_email_exists(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    username = random_email()
    password = random_lower_string()
    user = user_service.create_user(session=db, email=username, password=password)

    data = {"email": user.email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


def test_update_password_me_same_password_error(
    client: TestClient, user_factory: UserFactory
) -> None:
    user = user_factory.create(password="password")
    data = {
        "current_password": "password",
        "new_password": "password",
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert (
        updated_user["detail"] == "New password cannot be the same as the current one"
    )


def test_register_user(client: TestClient, db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    full_name = random_lower_string()
    data = {"email": username, "password": password, "full_name": full_name}
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json=data,
    )
    assert r.status_code == 200
    created_user = r.json()
    assert created_user["email"] == username
    assert created_user["full_name"] == full_name

    user_query = select(DbUser).where(DbUser.email == username)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == username
    assert user_db.full_name == full_name
    assert verify_password(password, user_db.hashed_password)


def test_register_user_already_exists_error(
    client: TestClient, user_factory: UserFactory
) -> None:
    user = user_factory.create()
    password = random_lower_string()
    full_name = random_lower_string()
    data = {
        "email": user.email,
        "password": password,
        "full_name": full_name,
    }
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json=data,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "The user with this email already exists in the system"


def test_update_user(
    client: TestClient, db: Session, user_factory: UserFactory
) -> None:
    user = user_factory.create(is_superuser=True, password="password")
    data = {"full_name": "Updated_full_name"}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()

    assert updated_user["full_name"] == "Updated_full_name"

    user_query = select(DbUser).where(DbUser.email == user.email)
    user_db = db.exec(user_query).first()
    db.refresh(user_db)
    assert user_db
    assert user_db.full_name == "Updated_full_name"


def test_update_user_not_exists(client: TestClient, user_factory: UserFactory) -> None:
    user = user_factory.create(is_superuser=True, password="password")
    data = {"full_name": "Updated_full_name"}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=data,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "The user with this id does not exist in the system"


def test_update_user_email_exists(
    client: TestClient, user_factory: UserFactory
) -> None:
    user = user_factory.create(is_superuser=True, password="password")
    password = random_lower_string()
    password2 = random_lower_string()
    user_factory.create(password=password)
    user2 = user_factory.create(password=password2)

    data = {"email": user2.email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


def test_delete_user_me(client: TestClient, db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = user_service.create_user(session=db, email=email, password=password)
    user_id = user.id

    login_data = {
        "username": email,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
    )
    assert r.status_code == 200
    deleted_user = r.json()
    assert deleted_user["message"] == "User deleted successfully"
    result = db.exec(select(DbUser).where(DbUser.id == user_id)).first()
    assert result is None

    user_query = select(DbUser).where(DbUser.id == user_id)
    user_db = db.exec(user_query).first()
    assert user_db is None


def test_delete_user_me_as_superuser(
    client: TestClient, user_factory: UserFactory
) -> None:
    user = user_factory.create(is_superuser=True, password="password")
    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert r.status_code == 403
    response = r.json()
    assert response["detail"] == "Super users are not allowed to delete themselves"


def test_delete_user_super_user(
    client: TestClient, db: Session, user_factory: UserFactory
) -> None:
    super_user = user_factory.create(is_superuser=True, password="password")
    password = random_lower_string()
    user = user_factory.create(password=password)
    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=user_authentication_headers(
            client=client, email=super_user.email, password="password"
        ),
    )
    assert r.status_code == 200
    deleted_user = r.json()
    assert deleted_user["message"] == "User deleted successfully"
    result = db.exec(select(DbUser).where(DbUser.id == user.id)).first()
    assert result is None


def test_delete_user_not_found(client: TestClient, user_factory: UserFactory) -> None:
    super_user = user_factory.create(is_superuser=True, password="password")
    r = client.delete(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=user_authentication_headers(
            client=client, email=super_user.email, password="password"
        ),
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_delete_user_current_super_user_error(
    client: TestClient, user_factory: UserFactory
) -> None:
    super_user = user_factory.create(
        username="superuser@admin.com", is_superuser=True, password="password"
    )
    r = client.delete(
        f"{settings.API_V1_STR}/users/{super_user.id}",
        headers=user_authentication_headers(
            client=client, email=super_user.email, password="password"
        ),
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Super users are not allowed to delete themselves"


def test_delete_user_without_privileges(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    email = random_email()
    password = random_lower_string()
    user = user_service.create_user(session=db, email=email, password=password)

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"


def test_update_user_model_preferences(
    client: TestClient, db: Session, user_factory: UserFactory
) -> None:
    user = user_factory.create(password="password")
    data = {
        "llm_model": "gpt-4",
        "openai_api_url": "https://api.openai.com/v1",
        "openai_api_key": "sk-1234567890abcdef",
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/model-preferences",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["llm_model"] == "gpt-4"
    assert updated_user["openai_api_url"] == "https://api.openai.com/v1"
    assert updated_user["openai_api_key"] == "sk-1234567890abcdef"

    user_query = select(DbUser).where(DbUser.email == user.email)
    user_db = db.exec(user_query).first()
    db.refresh(user_db)
    assert user_db
    assert user_db.llm_model == "gpt-4"
    assert user_db.openai_api_url == "https://api.openai.com/v1"
    assert user_db.openai_api_key == "sk-1234567890abcdef"
