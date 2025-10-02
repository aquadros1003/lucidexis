import uuid

from sqlmodel import Field

from core.base_model import SQLModelBase


class Document(SQLModelBase, table=True):
    __tablename__ = "document"

    filename: str = Field(max_length=255)
    content_type: str = Field(max_length=100)

    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)


class DocumentChunk(SQLModelBase, table=True):
    __tablename__ = "chunk"

    chunk_index: int
    content: str

    document_id: uuid.UUID = Field(foreign_key="document.id", index=True)
