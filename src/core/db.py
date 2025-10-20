from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import declarative_base
from sqlmodel import Session, SQLModel, create_engine

from core.config import settings

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

Base = declarative_base(metadata=SQLModel.metadata)


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    pass


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
