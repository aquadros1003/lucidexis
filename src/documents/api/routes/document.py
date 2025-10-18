import logging
import uuid
from typing import Any

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

import documents.domain.services.document as document_service
from core.config import settings
from documents.api.schemas.document import DocumentUploadResponse
from users.deps import CurrentUser, SessionDep

router = APIRouter(prefix="/documents", tags=["documents"])

logger = logging.getLogger(__name__)


@router.post("/", response_model=DocumentUploadResponse)
async def upload_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> Any:
    try:
        document = document_service.add_document(
            session=session,
            owner_id=current_user.id,
            filename=file.filename,
            content_type=file.content_type,
        )
        out_file_path = f"{settings.DOCUMENTS_DIR}/{document.id}"
        logger.info(f"Attempting to save document to: {out_file_path}")
        async with aiofiles.open(out_file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
        logger.info(f"Successfully saved document {document.id} to {out_file_path}")
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            is_processed=document.is_processed,
        )
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.get("/{document_id}")
def download_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID,
) -> FileResponse:
    document = document_service.get_document_by_id(
        session=session, document_id=str(document_id)
    )
    if not document or document.owner_id != current_user.id:
        logger.warning(
            f"Document not found or access denied {document_id=}, {current_user.id=}"
        )
        raise HTTPException(status_code=404, detail="Document not found")
    file_path = f"{settings.DOCUMENTS_DIR}/{document.id}"
    return FileResponse(
        path=file_path,
        media_type=document.content_type,
        filename=document.filename,
    )
