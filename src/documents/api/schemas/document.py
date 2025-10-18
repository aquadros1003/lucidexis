from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel


class DocumentUpload(BaseModel):
    file: UploadFile


class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    is_processed: bool
