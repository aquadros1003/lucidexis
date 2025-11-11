from datetime import datetime
from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel


class DocumentUpload(BaseModel):
    file: UploadFile
    description: str


class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    is_processed: bool


class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str


class DocumentChunkListResponse(BaseModel):
    data: list[DocumentChunkResponse]
    count: int


class DocumentPublic(BaseModel):
    id: UUID
    created_at: datetime
    filename: str
    file_size: int
    content_type: str
    description: str
    is_processed: bool
    download_url: str


class DocumentsPublic(BaseModel):
    data: list[DocumentPublic]
    count: int
