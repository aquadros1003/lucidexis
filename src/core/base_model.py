import uuid
from datetime import UTC, datetime

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, SQLModel


class SQLModelBase(SQLModel):
    """Base class for SQLModel models."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True), nullable=False, onupdate=datetime.now
        ),
    )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"
