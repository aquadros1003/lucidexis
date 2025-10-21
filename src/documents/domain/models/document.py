import uuid
from datetime import datetime
from typing import TYPE_CHECKING

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


class Document(SQLModel, table=True):
    __tablename__ = "document"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        ),
    )

    filename: str = Field(max_length=255)
    content_type: str = Field(max_length=100)
    file_path: str = Field(max_length=500)

    is_processed: bool = Field(default=False, nullable=False)

    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    owner: "User" = Relationship(back_populates="documents")

    chunks: list["DocumentChunk"] = Relationship(
        back_populates="document", cascade_delete=True
    )

    def __repr__(self) -> str:
        return f"Document(filename={self.filename}, owner_id={self.owner_id})"

    def __str__(self) -> str:
        return f"Document(filename={self.filename}, owner_id={self.owner_id})"


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunk"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        ),
    )

    chunk_index: int
    content: str

    document_id: uuid.UUID = Field(foreign_key="document.id", index=True)
    document: "Document" = Relationship(back_populates="chunks")

    def __repr__(self) -> str:
        return f"DocumentChunk(document_id={self.document_id}, chunk_index={self.chunk_index})"

    def __str__(self) -> str:
        return f"DocumentChunk(document_id={self.document_id}, chunk_index={self.chunk_index})"
