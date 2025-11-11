import logging
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse

import documents.domain.services.document as document_service
from core.config import settings
from core.db import SessionDep
from documents.api.schemas.document import (
    DocumentPublic,
    DocumentsPublic,
    DocumentUploadResponse,
)
from documents.domain.services.chunk import chunk_document, embed_document_chunks
from users.deps import CurrentUser

router = APIRouter(prefix="/documents", tags=["documents"])

logger = logging.getLogger(__name__)


@router.get("/", response_model=DocumentsPublic)
async def documents(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = 100,
    offset: int = 0,
) -> DocumentsPublic:
    documents = document_service.get_owner_documents(
        session=session, owner_id=current_user.id, limit=limit, offset=offset
    )
    return DocumentsPublic(
        data=[
            DocumentPublic(
                id=document.id,
                created_at=document.created_at,
                filename=document.filename,
                file_size=document.file_size,
                content_type=document.content_type,
                description=document.description,
                is_processed=document.is_processed,
                download_url=f"{settings.BACKEND_HOST}/api/v1/documents/download/{document.id}",
            )
            for document in documents
        ],
        count=document_service.get_owner_documents_count(
            session=session, owner_id=current_user.id
        ),
    )


@router.get("/{document_id}", response_model=DocumentPublic)
async def get_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID,
) -> DocumentPublic:
    document = document_service.get_document_by_id(
        session=session, document_id=document_id
    )
    if not document or document.owner_id != current_user.id:
        logger.warning(
            f"Document not found or access denied {document=}, {current_user=}"
        )
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentPublic(
        id=document.id,
        created_at=document.created_at,
        filename=document.filename,
        file_size=document.file_size,
        content_type=document.content_type,
        is_processed=document.is_processed,
        description=document.description,
        download_url=f"{settings.BACKEND_HOST}/api/v1/documents/download/{document.id}",
    )


@router.post("/", response_model=DocumentUploadResponse)
async def upload_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    description: str = Form(...),
    chunk_size: int = 1024,
    request: Request,
    background_tasks: BackgroundTasks,
) -> DocumentUploadResponse:
    try:
        out_file_path = await document_service.save_document_to_path(
            file=await file.read()
        )
        document = document_service.add_document(
            session=session,
            owner_id=current_user.id,
            file_path=out_file_path,
            file_size=len(file.file.read()),
            filename=file.filename,
            content_type=file.content_type,
            description=description,
        )
        background_tasks.add_task(
            chunk_document,
            document_id=document.id,
            chunk_size=chunk_size,
            session=session,
        )
        if not hasattr(request.app.state, "embedding_model"):
            logger.error("Embedding model not found in app state")
        else:
            background_tasks.add_task(
                embed_document_chunks,
                document_id=document.id,
                session=session,
                embedding_model=request.app.state.embedding_model,
            )
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            is_processed=document.is_processed,
        )
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.get("/download/{document_id}")
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
