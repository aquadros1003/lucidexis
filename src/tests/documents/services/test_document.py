from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
from sqlmodel import Session

import documents.domain.services.document as document_service
from documents.domain.models.document import DocumentCategory
from tests.factories.document import DocumentChunkFactory, DocumentFactory
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
        category=DocumentCategory.LEGAL,
        content_type=content_type,
        description="Test document description",
    )
    assert document.filename == filename
    assert document.content_type == content_type
    assert document.category == DocumentCategory.LEGAL


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


def test_get_document_predictions(
    db: Session,
    user_factory: UserFactory,
    document_factory: DocumentFactory,
    document_chunk_factory: DocumentChunkFactory,
) -> None:
    owner = user_factory.create()
    document = document_factory.create(owner=owner)

    document_chunk_factory.create(
        document=document,
        chunk_index=0,
        content="Python is a programming language",
        embedding=np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
    )
    document_chunk_factory.create(
        document=document,
        chunk_index=1,
        content="JavaScript is also a programming language",
        embedding=np.array([0.2, 0.3, 0.4, 0.5, 0.6]),
    )
    mock_embedding_model = MagicMock()
    mock_embedding_model.encode.return_value = np.array([0.15, 0.25, 0.35, 0.45, 0.55])

    result = document_service.get_document_predictions(
        embedding_model=mock_embedding_model,
        session=db,
        owner_id=owner.id,
        search_query="programming",
    )

    assert len(result) > 0
    assert result[0][0].id == document.id
    assert result[0][1] in [
        "Python is a programming language",
        "JavaScript is also a programming language",
    ]
