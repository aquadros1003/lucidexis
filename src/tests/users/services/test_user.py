from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

import users.domain.services.user as user_service
from core.security import verify_password
from tests.utils.utils import random_email, random_lower_string
from users.api.schemas.user import UserUpdate
from users.domain.models.user import User as DbUser


def test_create_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = user_service.create_user(session=db, email=email, password=password)
    assert user.email == email
    assert hasattr(user, "hashed_password")


def test_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = user_service.create_user(session=db, email=email, password=password)
    authenticated_user = user_service.authenticate(
        session=db, email=email, password=password
    )
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = user_service.authenticate(session=db, email=email, password=password)
    assert user is None


def test_check_if_user_is_active(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = user_service.create_user(session=db, email=email, password=password)
    assert user.is_active is True


def test_check_if_user_is_superuser(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = user_service.create_user(
        session=db, email=email, password=password, is_superuser=True
    )
    assert user.is_superuser is True


def test_check_if_user_is_superuser_normal_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = user_service.create_user(session=db, email=email, password=password)
    assert user.is_superuser is False


def test_get_user(db: Session) -> None:
    password = random_lower_string()
    email = random_email()
    user = user_service.create_user(session=db, email=email, password=password)
    user_2 = db.get(DbUser, user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    password = random_lower_string()
    email = random_email()
    user = user_service.create_user(session=db, email=email, password=password)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    if user.id is not None:
        user_service.update_user(session=db, db_user=user, user_in=user_in_update)
    user_2 = db.get(DbUser, user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)
