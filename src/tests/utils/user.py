from fastapi.testclient import TestClient
from sqlmodel import Session

import users.domain.services.user as user_service
from core.config import settings
from tests.utils.utils import random_email, random_lower_string
from users.api.schemas.user import UserUpdate
from users.domain.models.user import User as DbUser


def user_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user(db: Session) -> DbUser:
    email = random_email()
    password = random_lower_string()
    user = user_service.create_user(session=db, email=email, password=password)
    return user


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = random_lower_string()
    user = user_service.get_user_by_email(session=db, email=email)
    if not user:
        user = user_service.create_user(session=db, email=email, password=password)
    else:
        user_in_update = UserUpdate(password=password)
        if not user.id:
            raise Exception("User id not set")
        user = user_service.update_user(
            session=db, db_user=user, user_in=user_in_update
        )

    return user_authentication_headers(client=client, email=email, password=password)
