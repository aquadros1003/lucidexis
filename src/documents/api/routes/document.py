import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

import documents.domain.services.document as document_service
from core.config import settings
from core.db import SessionDep
from documents.api.schemas.document import DocumentUploadResponse
from documents.domain.services.chunk import chunk_document
from users.deps import CurrentUser

router = APIRouter(prefix="/documents", tags=["documents"])

logger = logging.getLogger(__name__)


@router.post("/", response_model=DocumentUploadResponse)
async def upload_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    chunk_size: int = 1024,
    background_tasks: BackgroundTasks,
) -> Any:
    try:
        out_file_path = Path(
            f"{settings.DOCUMENTS_DIR}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        logger.info(f"Attempting to save document to: {out_file_path}")
        async with aiofiles.open(out_file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
        logger.info(f"Document saved to: {out_file_path}")
        document = document_service.add_document(
            session=session,
            owner_id=current_user.id,
            file_path=out_file_path,
            filename=file.filename,
            content_type=file.content_type,
        )
        background_tasks.add_task(
            chunk_document,
            document_id=document.id,
            chunk_size=chunk_size,
            session=session,
        )
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
        session=session, document_id=document_id
    )
    if not document or document.owner_id != current_user.id:
        logger.warning(
            f"Document not found or access denied {document=}, {current_user=}"
        )
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(
        path=document.file_path,
        media_type=document.content_type,
        filename=document.filename,
    )
