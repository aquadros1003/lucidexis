import logging
import uuid
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import aiofiles
from sqlalchemy import Integer
from sqlmodel import Session, cast, func, select

from core.config import settings
from documents.api.filters.document import DocumentFilter
from documents.domain.models.document import Document as DbDocument

logger = logging.getLogger(__name__)


def add_document(
    *,
    session: Session,
    owner_id: uuid.UUID,
    file_path: Path,
    file_size: int,
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
) -> DbDocument:
    if description is not None:
        document.description = description
    if is_archived is not None:
        document.is_archived = is_archived
    if is_favorite is not None:
        document.is_favorite = is_favorite
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
        f"{settings.DOCUMENTS_DIR}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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


def get_owner_documents(
    *,
    session: Session,
    owner_id: uuid.UUID,
    filter: DocumentFilter,
    limit: int,
    offset: int,
) -> Sequence[DbDocument]:
    query = select(DbDocument).where(DbDocument.owner_id == owner_id)
    query = filter.filter(query)
    query = filter.sort(query)
    query = query.offset(offset).limit(limit)
    results = session.exec(query)
    return results.all()


def get_owner_documents_count(
    *, session: Session, owner_id: uuid.UUID, filter: DocumentFilter
) -> int:
    query = (
        select(func.count())
        .select_from(DbDocument)
        .where(DbDocument.owner_id == owner_id)
    )
    query = filter.filter(query)
    result = session.exec(query)
    return result.one()


def get_owner_documents_stats(*, session: Session, owner_id: uuid.UUID) -> dict:
    statement = select(
        func.count().label("total_documents"),
        func.sum(cast(DbDocument.is_archived, Integer)).label("archived_documents"),
        func.sum(cast(DbDocument.is_favorite, Integer)).label("favorite_documents"),
    ).where(DbDocument.owner_id == owner_id)
    result = session.exec(statement).one()
    return {
        "total_documents": result[0],
        "archived_documents": result[1],
        "favorite_documents": result[2],
    }


def get_document_markdown_preview(*, document: DbDocument) -> str:
    chunks = sorted(document.chunks, key=lambda c: c.chunk_index)
    markdown_preview = "\n".join(chunk.content for chunk in chunks)
    return markdown_preview
