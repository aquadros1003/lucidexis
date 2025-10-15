import uuid
from datetime import datetime

from sqlmodel import TIMESTAMP, Column, FetchedValue, Field, SQLModel, text


class Document(SQLModel, table=True):
    __tablename__ = "document"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )

    filename: str = Field(max_length=255)
    content_type: str = Field(max_length=100)

    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunk"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )

    chunk_index: int
    content: str

    document_id: uuid.UUID = Field(foreign_key="document.id", index=True)
