import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiofiles
from sentence_transformers import SentenceTransformer
from sqlalchemy import Integer, case
from sqlmodel import Session, cast, col, func, select

from core.config import settings
from documents.api.filters.document import DocumentFilter
from documents.domain.models.document import Document as DbDocument
from documents.domain.models.document import DocumentCategory
from documents.domain.models.document import DocumentChunk as DbDocumentChunk

logger = logging.getLogger(__name__)

COSINE_SIMILARITY_THRESHOLD = 0.80


def add_document(
    *,
    session: Session,
    owner_id: uuid.UUID,
    file_path: Path,
    file_size: int,
    category: DocumentCategory,
    filename: str | None,
    content_type: str | None,
    description: str | None = None,
) -> DbDocument:
    logger.info(f"Adding document for {owner_id=}, {filename=}")
    db_obj = DbDocument.model_validate(
        {
            "filename": filename,
            "file_size": file_size,
            "content_type": content_type,
            "owner_id": owner_id,
            "file_path": str(file_path),
            "description": description,
            "category": category,
        }
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_document(
    *,
    session: Session,
    document: DbDocument,
    description: str | None = None,
    is_archived: bool | None = None,
    is_favorite: bool | None = None,
    category: DocumentCategory | None = None,
) -> DbDocument:
    logger.info(f"Updating document {document.id=}, {document.filename=}")
    if description is not None:
        document.description = description
    if is_archived is not None:
        document.is_archived = is_archived
    if is_favorite is not None:
        document.is_favorite = is_favorite
    if category is not None:
        document.category = category
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def delete_document(*, session: Session, document: DbDocument) -> None:
    logger.info(f"Deleting document {document.id=}, {document.filename=}")
    session.delete(document)
    session.commit()


async def save_document_to_path(*, file: bytes) -> Path:
    out_file_path = Path(
        f"{settings.DOCUMENTS_DIR}/{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    )
    logger.info(f"Saving document to path: {out_file_path=}")
    async with aiofiles.open(out_file_path, "wb") as out_file:
        await out_file.write(file)
    logger.info(f"Document saved to path: {out_file_path=}")
    return out_file_path


def get_document_by_id(
    *, session: Session, document_id: uuid.UUID
) -> DbDocument | None:
    return session.get(DbDocument, document_id)


def visit_document(*, session: Session, document: DbDocument) -> None:
    logger.info(f"Marking document as visited {document.id=}, {document.filename=}")
    document.mark_visited()
    session.add(document)
    session.commit()
    session.refresh(document)


def get_owner_documents(
    *,
    session: Session,
    owner_id: uuid.UUID,
    filter: DocumentFilter,
    recently_visited: bool | None = None,
    limit: int,
    offset: int,
) -> Sequence[DbDocument]:
    query = select(DbDocument).where(DbDocument.owner_id == owner_id)
    if recently_visited:
        query = query.where(
            col(DbDocument.visited_at) is not None,
            col(DbDocument.visited_at) > datetime.now(UTC) - timedelta(days=7),
        ).order_by(col(DbDocument.visited_at).desc())
    query = filter.filter(query)
    query = filter.sort(query)
    query = query.offset(offset).limit(limit)
    results = session.exec(query)
    return results.all()


def get_owner_documents_count(
    *,
    session: Session,
    owner_id: uuid.UUID,
    filter: DocumentFilter,
    recently_visited: bool | None = None,
) -> int:
    query = (
        select(func.count())
        .select_from(DbDocument)
        .where(DbDocument.owner_id == owner_id)
    )
    if recently_visited:
        query = query.where(
            col(DbDocument.visited_at) is not None,
            col(DbDocument.visited_at) > datetime.now(UTC) - timedelta(days=7),
        )
    query = filter.filter(query)
    result = session.exec(query)
    return result.one()


def get_owner_documents_stats(*, session: Session, owner_id: uuid.UUID) -> dict:
    select_columns = [
        func.count().label("total_documents"),
        func.sum(cast(DbDocument.is_archived, Integer)).label("archived_documents"),
        func.sum(cast(DbDocument.is_favorite, Integer)).label("favorite_documents"),
    ]
    for category in DocumentCategory:
        select_columns.append(
            func.sum(
                case(
                    (DbDocument.category == category, 1),  # type: ignore[arg-type]
                    else_=0,
                )
            ).label(f"{category.name.lower()}_documents")
        )
    statement = select(*select_columns).where(DbDocument.owner_id == owner_id)
    result = session.exec(statement).one()
    result_dict = {
        "total_documents": result.total_documents or 0,  # type: ignore
        "archived_documents": result.archived_documents or 0,  # type: ignore
        "favorite_documents": result.favorite_documents or 0,  # type: ignore
    }
    for category in DocumentCategory:
        result_dict[f"{category.name.lower()}_documents"] = (
            getattr(result, f"{category.name.lower()}_documents") or 0
        )
    return result_dict


def get_document_markdown_preview(
    *, document: DbDocument, chunk_limit: int | None = None
) -> str:
    chunks = sorted(document.chunks, key=lambda c: c.chunk_index)
    chunks = chunks[:chunk_limit] if chunk_limit is not None else chunks
    markdown_preview = "\n".join(chunk.content for chunk in chunks)
    return markdown_preview


def get_document_predictions(
    *,
    embedding_model: SentenceTransformer,
    session: Session,
    owner_id: uuid.UUID,
    search_query: str,
) -> list[tuple[DbDocument, str, float]]:
    query_embedding = embedding_model.encode(
        search_query, convert_to_numpy=True, show_progress_bar=False
    )
    statement = (
        select(
            DbDocument,
            DbDocumentChunk.content,
            (1 - DbDocumentChunk.embedding.cosine_distance(query_embedding)).label(  # type: ignore
                "accuracy"
            ),
        )
        .join(DbDocumentChunk)
        .where(
            DbDocument.owner_id == owner_id,
            DbDocumentChunk.embedding is not None,
            DbDocumentChunk.embedding.cosine_distance(query_embedding)  # type: ignore
            < 1 - COSINE_SIMILARITY_THRESHOLD,
        )
        .distinct(DbDocument.id)  # type: ignore
        .order_by(
            DbDocument.id,  # type: ignore
            DbDocumentChunk.embedding.cosine_distance(query_embedding),  # type: ignore
        )
        .limit(5)
    )
    results = session.exec(statement).all()
    predictions = [
        (doc, content, float(accuracy)) for doc, content, accuracy in results
    ]
    return predictions
