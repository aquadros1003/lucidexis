import logging
import uuid
from pathlib import Path

from sqlmodel import Session

from documents.domain.models.document import Document as DbDocument

logger = logging.getLogger(__name__)


def add_document(
    *,
    session: Session,
    owner_id: uuid.UUID,
    file_path: Path,
    filename: str | None,
    content_type: str | None,
) -> DbDocument:
    logger.info(f"Adding document for owner_id: {owner_id}, filename: {filename}")
    db_obj = DbDocument.model_validate(
        {
            "filename": filename,
            "content_type": content_type,
            "owner_id": owner_id,
            "file_path": str(file_path),
        }
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_document_by_id(
    *, session: Session, document_id: uuid.UUID
) -> DbDocument | None:
    return session.get(DbDocument, document_id)
