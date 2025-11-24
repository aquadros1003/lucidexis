from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_factoryboy import register
from sqlmodel import Session, SQLModel

from core.db import engine
from tests.factories.document import DocumentChunkFactory, DocumentFactory
from tests.factories.user import UserFactory
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@asynccontextmanager
async def lifespan_override(app: FastAPI) -> AsyncGenerator:
    app.state.embedding_model = None
    yield


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator:
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
    from main import app

    app.router.lifespan_context = lifespan_override
    test_client = TestClient(app)
    yield test_client


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
    DocumentChunkFactory._meta.sqlalchemy_session = db  # type: ignore
    UserFactory._meta.sqlalchemy_session = db  # type: ignore


register(DocumentFactory)
register(DocumentChunkFactory)
register(UserFactory)
