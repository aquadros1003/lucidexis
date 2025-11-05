from pathlib import Path

from sqlmodel import Session, select

import documents.domain.services.chunk as chunk_service
from documents.domain.models.document import DocumentChunk as DbDocumentChunk
from tests.factories.document import DocumentFactory
from tests.factories.user import UserFactory


def test_chunk_document(
    user_factory: UserFactory,
    document_factory: DocumentFactory,
    tmp_path: Path,
    db: Session,
) -> None:
    user = user_factory.create()
    document_content = "This is a test document. " * 50
    document_file = tmp_path / "test_document.txt"
    document_file.write_text(document_content, encoding="utf-8")
    document = document_factory.create(
        user_id=user.id,
        file_path=str(document_file),
        is_processed=False,
    )
    chunk_size = 100
    chunk_service.chunk_document(
        session=db,
        document_id=document.id,
        chunk_size=chunk_size,
    )
    db.refresh(document)

    chunks = db.exec(
        select(DbDocumentChunk).where(DbDocumentChunk.document_id == document.id)
    ).all()
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk.content) <= chunk_size
