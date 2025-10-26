import logging
import uuid
from pathlib import Path

from pydantic import ValidationError
from semantic_text_splitter import TextSplitter

from core.db import SessionDep
from documents.domain.models.document import Document as DbDocument
from documents.domain.models.document import DocumentChunk as DbDocumentChunk
from documents.domain.services.extractor import EXTRACTOR_MAP

logger = logging.getLogger(__name__)


def chunk_document(
    *,
    document_id: uuid.UUID,
    chunk_size: int,
    session: SessionDep,
) -> None:
    logger.info(f"Chunking document {document_id=} with {chunk_size=}")
    document: DbDocument | None = session.get(DbDocument, document_id)
    if not document:
        logger.error(f"Document {document_id=} not found for chunking.")
        return
    try:
        content = EXTRACTOR_MAP[document.content_type].extract_text(
            Path(document.file_path)
        )
        splitter = TextSplitter(capacity=chunk_size, overlap=chunk_size // 10)
        chunks = splitter.chunks(content)
        for idx, chunk in enumerate(chunks):
            logger.debug(f"Creating chunk {idx} for {document_id=}")
            db_chunk = DbDocumentChunk.model_validate(
                {
                    "document_id": document_id,
                    "chunk_index": idx,
                    "content": chunk,
                }
            )
            session.add(db_chunk)
        document.is_processed = True
        session.commit()
        logger.info(f"Successfully chunked {document_id=} into {len(chunks)} chunks.")
    except ValidationError as ve:
        logger.error(f"Chunk content validation error: {ve.errors()}")
    except Exception as e:
        logger.error(f"Error while chunking {document_id=}: {e}")
