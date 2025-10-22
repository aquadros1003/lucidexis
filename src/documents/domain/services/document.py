import logging
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
from sqlmodel import Session

from core.config import settings
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


async def save_document_to_path(*, file: bytes) -> Path:
    out_file_path = Path(
        f"{settings.DOCUMENTS_DIR}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    logger.info(f"Saving document to path: {out_file_path}")
    async with aiofiles.open(out_file_path, "wb") as out_file:
        await out_file.write(file)
    logger.info(f"Document saved to path: {out_file_path}")
    return out_file_path
