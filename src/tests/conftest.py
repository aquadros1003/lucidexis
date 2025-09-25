from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from pytest_factoryboy import register
from sqlmodel import Session, delete

from core.db import engine, init_db
from main import app
from tests.users.factories.user import UserFactory
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers
from users.domain.models.user import User


@pytest.fixture(autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(User)
        session.execute(statement)
        session.commit()
        session.rollback()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture
def normal_user_token_headers(
    client: TestClient, db: Session, user: UserFactory | None = None
) -> dict[str, str]:
    user = UserFactory() if user is None else user
    return authentication_token_from_email(client=client, email=user.email, db=db)


@pytest.fixture(autouse=True)
def set_session_for_factories(db: Session):
    UserFactory._meta.sqlalchemy_session = db


register(UserFactory)
