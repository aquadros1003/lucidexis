import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.dialects.postgresql import JSONB
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
    from users.domain.models.user import User


class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        ),
    )

    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    user: "User" = Relationship(back_populates="conversations")

    messages: list["Message"] = Relationship(
        back_populates="conversation",
        cascade_delete=True,
        sa_relationship_kwargs={"order_by": "Message.created_at.asc()"},
    )

    def __repr__(self) -> str:
        return f"Conversation(id={self.id}, user_id={self.user_id})"

    def __str__(self) -> str:
        return f"Conversation(id={self.id}, user_id={self.user_id})"


class MessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(SQLModel, table=True):
    __tablename__ = "message"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        ),
    )

    content: str = Field(nullable=False)
    role: MessageRole = Field(nullable=False)
    additional_data: dict | None = Field(sa_column=Column(JSONB))

    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", index=True)
    conversation: "Conversation" = Relationship(back_populates="messages")

    def __repr__(self) -> str:
        return (
            f"Message(id={self.id}, role={self.role}, content={self.content[:20]}...)"
        )

    def __str__(self) -> str:
        return (
            f"Message(id={self.id}, role={self.role}, content={self.content[:20]}...)"
        )
