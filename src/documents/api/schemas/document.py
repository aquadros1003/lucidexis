from datetime import datetime
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel

from documents.domain.models.document import DocumentCategory


class DocumentUpload(BaseModel):
    chunk_size: int = 1024
    description: str = ""
    category: DocumentCategory = DocumentCategory.TECHNICAL

    @classmethod
    def as_form(
        cls,
        chunk_size: int = Form(1024),
        description: str = Form(""),
        category: DocumentCategory = Form("technical"),
    ) -> "DocumentUpload":
        return cls(
            chunk_size=chunk_size,
            description=description,
            category=category,
        )


class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    is_processed: bool
    category: DocumentCategory


class DocumentUpdate(BaseModel):
    description: str | None = None
    is_archived: bool | None = None
    is_favorite: bool | None = None
    category: DocumentCategory | None = None


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
    category: DocumentCategory
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
    technical_documents: int
    marketing_documents: int
    sales_documents: int
    hr_documents: int
    finance_documents: int
    legal_documents: int
    product_documents: int


class DocumentPredictionRequest(BaseModel):
    search_query: str


class DocumentPrediction(BaseModel):
    document: DocumentPublic
    chunk_content: str
    accuracy: float


class DocumentPredictionResponse(BaseModel):
    predictions: list[DocumentPrediction]
