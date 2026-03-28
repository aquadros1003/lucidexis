import uuid
from datetime import UTC, datetime

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

from chat.domain.models.message import Conversation
from documents.domain.models.document import Document


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(UTC),
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
    locale: str = Field(default="pl_PL", max_length=5)

    # LLM model preferences
    llm_model: str | None = None
    openai_api_url: str | None = None
    openai_api_key: str | None = None
    openai_system_prompt: str | None = None

    conversations: list["Conversation"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    documents: list["Document"] = Relationship(
        back_populates="owner", cascade_delete=True
    )

    def __repr__(self) -> str:
        return f"User(email={self.email}, is_active={self.is_active})"

    def __str__(self) -> str:
        return f"User(email={self.email}, is_active={self.is_active})"
