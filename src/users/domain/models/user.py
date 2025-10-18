import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import (
    TIMESTAMP,
    Column,
    FetchedValue,
    Field,
    Relationship,
    SQLModel,
    text,
)

if TYPE_CHECKING:
    from documents.domain.models.document import Document


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        ),
    )

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    hashed_password: str

    documents: list["Document"] = Relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"User(email={self.email}, is_active={self.is_active})"

    def __str__(self) -> str:
        return f"User(email={self.email}, is_active={self.is_active})"
