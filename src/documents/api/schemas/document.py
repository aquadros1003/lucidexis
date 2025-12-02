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


class DocumentUpdate(BaseModel):
    description: str | None = None
    is_archived: bool | None = None
    is_favorite: bool | None = None


class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str


class DocumentChunkListResponse(BaseModel):
    data: list[DocumentChunkResponse]
    count: int


class OwnerPublic(BaseModel):
    id: UUID
    email: str
    full_name: str | None


class DocumentPublic(BaseModel):
    id: UUID
    created_at: datetime
    filename: str
    file_size: int
    content_type: str
    description: str
    is_processed: bool
    is_archived: bool
    is_favorite: bool
    download_url: str
    owner: OwnerPublic


class DocumentsPublic(BaseModel):
    data: list[DocumentPublic]
    count: int


class DocumentStats(BaseModel):
    total_documents: int
    archived_documents: int
    favorite_documents: int


class DocumentPredictionRequest(BaseModel):
    search_query: str


class DocumentPrediction(BaseModel):
    document: DocumentPublic
    chunk_content: str


class DocumentPredictionResponse(BaseModel):
    predictions: list[DocumentPrediction]
