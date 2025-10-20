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
        filename=filename,
        content_type=content_type,
    )
    assert document.filename == filename
    assert document.content_type == content_type


def test_get_document_by_id(
    db: Session, user_factory: UserFactory, document_factory: DocumentFactory
) -> None:
    owner = user_factory.create()
    filename = "sample_doc.txt"
    content_type = "text/plain"
    document = document_factory.create(
        owner_id=owner.id, filename=filename, content_type=content_type
    )
    fetched_document = document_service.get_document_by_id(
        session=db, document_id=document.id
    )
    assert fetched_document is not None
    assert fetched_document.id == document.id
    assert fetched_document.filename == filename
    assert fetched_document.content_type == content_type
