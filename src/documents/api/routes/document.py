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
from fastapi_filter import FilterDepends

import documents.domain.services.document as document_service
from core.config import settings
from core.db import SessionDep
from documents.api.filters.document import DocumentFilter
from documents.api.schemas.document import (
    DocumentPrediction,
    DocumentPredictionRequest,
    DocumentPredictionResponse,
    DocumentPublic,
    DocumentsPublic,
    DocumentStats,
    DocumentUpdate,
    DocumentUploadResponse,
    OwnerPublic,
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
    document_filter: DocumentFilter = FilterDepends(DocumentFilter),
    limit: int = 100,
    offset: int = 0,
) -> DocumentsPublic:
    documents = document_service.get_owner_documents(
        session=session,
        owner_id=current_user.id,
        filter=document_filter,
        limit=limit,
        offset=offset,
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
                is_archived=document.is_archived,
                is_favorite=document.is_favorite,
                download_url=f"{settings.BACKEND_HOST}/api/v1/documents/download/{document.id}",
                owner=OwnerPublic(
                    id=document.owner.id,
                    email=document.owner.email,
                    full_name=document.owner.full_name,
                ),
            )
            for document in documents
        ],
        count=document_service.get_owner_documents_count(
            session=session, owner_id=current_user.id, filter=document_filter
        ),
    )


@router.get("/stats", response_model=DocumentStats)
async def get_documents_stats(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> DocumentStats:
    stats = document_service.get_owner_documents_stats(
        session=session, owner_id=current_user.id
    )
    return DocumentStats(**stats)


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
        is_archived=document.is_archived,
        is_favorite=document.is_favorite,
        description=document.description,
        download_url=f"{settings.BACKEND_HOST}/api/v1/documents/download/{document.id}",
        owner=OwnerPublic(
            id=document.owner.id,
            email=document.owner.email,
            full_name=document.owner.full_name,
        ),
    )


@router.get("/{document_id}/preview/markdown", response_model=str)
async def get_document_markdown_preview(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID,
) -> str:
    document = document_service.get_document_by_id(
        session=session, document_id=document_id
    )
    if not document or document.owner_id != current_user.id:
        logger.warning(
            f"Document not found or access denied {document=}, {current_user=}"
        )
        raise HTTPException(status_code=404, detail="Document not found")
    markdown_preview = document_service.get_document_markdown_preview(document=document)
    return markdown_preview


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
            file_size=file.size or 0,
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


@router.patch("/{document_id}", response_model=DocumentPublic)
async def update_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID,
    document_update: DocumentUpdate,
) -> DocumentPublic:
    document = document_service.get_document_by_id(
        session=session, document_id=document_id
    )
    if not document or document.owner_id != current_user.id:
        logger.warning(
            f"Document not found or access denied {document=}, {current_user=}"
        )
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        updated_document = document_service.update_document(
            session=session,
            document=document,
            description=document_update.description,
            is_archived=document_update.is_archived,
            is_favorite=document_update.is_favorite,
        )
        return DocumentPublic(
            id=updated_document.id,
            created_at=updated_document.created_at,
            filename=updated_document.filename,
            file_size=updated_document.file_size,
            content_type=updated_document.content_type,
            is_processed=updated_document.is_processed,
            is_archived=updated_document.is_archived,
            is_favorite=updated_document.is_favorite,
            description=updated_document.description,
            download_url=f"{settings.BACKEND_HOST}/api/v1/documents/download/{updated_document.id}",
            owner=OwnerPublic(
                id=updated_document.owner.id,
                email=updated_document.owner.email,
                full_name=updated_document.owner.full_name,
            ),
        )
    except Exception as e:
        logger.error(f"Error updating document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update document")


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID,
) -> None:
    document = document_service.get_document_by_id(
        session=session, document_id=document_id
    )
    if not document or document.owner_id != current_user.id:
        logger.warning(
            f"Document not found or access denied {document=}, {current_user=}"
        )
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        document_service.delete_document(session=session, document=document)
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.post("/predict", response_model=DocumentPredictionResponse)
async def predict_document_relevance(
    *,
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
    prediction_request: DocumentPredictionRequest,
) -> DocumentPredictionResponse:
    try:
        if not hasattr(request.app.state, "embedding_model"):
            logger.error("Embedding model not found in app state")
        predictions = document_service.get_document_predictions(
            embedding_model=request.app.state.embedding_model,
            session=session,
            owner_id=current_user.id,
            search_query=prediction_request.search_query,
        )
        response = DocumentPredictionResponse(
            predictions=[
                DocumentPrediction(
                    document=DocumentPublic(
                        id=document.id,
                        created_at=document.created_at,
                        filename=document.filename,
                        file_size=document.file_size,
                        content_type=document.content_type,
                        is_processed=document.is_processed,
                        is_archived=document.is_archived,
                        is_favorite=document.is_favorite,
                        description=document.description,
                        download_url=f"{settings.BACKEND_HOST}/api/v1/documents/download/{document.id}",
                        owner=OwnerPublic(
                            id=document.owner.id,
                            email=document.owner.email,
                            full_name=document.owner.full_name,
                        ),
                    ),
                    chunk_content=content,
                )
                for document, content in predictions
            ]
        )
        return response
    except Exception as e:
        logger.error(f"Error predicting document relevance: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to predict document relevance"
        )
