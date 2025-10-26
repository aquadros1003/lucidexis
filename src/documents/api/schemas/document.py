from datetime import datetime
from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel


class DocumentUpload(BaseModel):
    file: UploadFile


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
    content_type: str
    is_processed: bool
    download_url: str


class DocumentsPublic(BaseModel):
    data: list[DocumentPublic]
    count: int
