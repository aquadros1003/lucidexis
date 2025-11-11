from pathlib import Path

from sqlmodel import Session

import documents.domain.services.document as document_service
from tests.factories.document import DocumentFactory
from tests.factories.user import UserFactory


def test_create_document(
    db: Session,
    user_factory: UserFactory,
    tmp_path: Path,
) -> None:
    owner = user_factory.create()
    filename = "test_document.pdf"
    content_type = "application/pdf"
    file_path = tmp_path / filename
    document = document_service.add_document(
        session=db,
        owner_id=owner.id,
        file_path=file_path,
        file_size=2048,
        filename=filename,
        content_type=content_type,
        description="Test document description",
    )
    assert document.filename == filename
    assert document.content_type == content_type


def test_get_document_by_id(
    db: Session,
    tmp_path: Path,
    user_factory: UserFactory,
    document_factory: DocumentFactory,
) -> None:
    owner = user_factory.create()
    filename = "sample_doc.txt"
    content_type = "text/plain"
    file_path = tmp_path / filename
    document = document_factory.create(
        owner_id=owner.id,
        filename=filename,
        content_type=content_type,
        file_path=str(file_path),
    )
    fetched_document = document_service.get_document_by_id(
        session=db, document_id=document.id
    )
    assert fetched_document is not None
    assert fetched_document.id == document.id
    assert fetched_document.filename == filename
    assert fetched_document.content_type == content_type
