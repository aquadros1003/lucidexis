from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from pytest_factoryboy import register
from sqlmodel import Session, SQLModel

from core.db import engine
from main import app
from tests.factories.document import DocumentFactory
from tests.factories.user import UserFactory
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None]:
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def db() -> Generator[Session]:
    with Session(engine) as session:
        try:
            session.rollback()
            yield session
        except Exception:
            session.rollback()
            raise


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture
def normal_user_token_headers(
    client: TestClient, db: Session, user: UserFactory | None = None
) -> dict[str, str]:
    normal_user = user if user else UserFactory.create()
    return authentication_token_from_email(
        client=client,
        email=normal_user.email,  # type: ignore
        db=db,
    )


@pytest.fixture(autouse=True)
def set_session_for_factories(db: Session) -> None:
    DocumentFactory._meta.sqlalchemy_session = db  # type: ignore
    UserFactory._meta.sqlalchemy_session = db  # type: ignore


register(DocumentFactory)
register(UserFactory)
