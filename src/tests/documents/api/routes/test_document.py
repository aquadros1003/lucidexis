from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session

from core.config import settings
from documents.domain.models.document import DocumentCategory
from tests.factories.document import DocumentChunkFactory, DocumentFactory
from tests.factories.user import UserFactory
from tests.utils.user import user_authentication_headers


def test_list_documents(
    client: TestClient, user_factory: UserFactory, document_factory: DocumentFactory
) -> None:
    user = user_factory.create()
    document_factory.create_batch(3, owner=user)
    response = client.get(
        f"{settings.API_V1_STR}/documents",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert len(data["data"]) == 3


def test_list_documents_filtered_by_category(
    client: TestClient, user_factory: UserFactory, document_factory: DocumentFactory
) -> None:
    user = user_factory.create()
    document_factory.create_batch(2, owner=user, category=DocumentCategory.MARKETING)
    document_factory.create_batch(3, owner=user, category=DocumentCategory.SALES)
    response = client.get(
        f"{settings.API_V1_STR}/documents?category=marketing",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["data"]) == 2
    for document in data["data"]:
        assert document["category"] == "marketing"


def test_get_document(
    db: Session,
    client: TestClient,
    user_factory: UserFactory,
    document_factory: DocumentFactory,
) -> None:
    user = user_factory.create()
    document = document_factory.create(owner=user)
    response = client.get(
        f"{settings.API_V1_STR}/documents/{document.id}",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    db.refresh(document)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(document.id)
    assert data["filename"] == document.filename
    assert data["owner"]["id"] == str(user.id)
    assert data["owner"]["email"] == user.email
    assert data["owner"]["full_name"] == user.full_name
    assert document.visited_at is not None


def test_filter_documents_by_is_favorite(
    client: TestClient, user_factory: UserFactory, document_factory: DocumentFactory
) -> None:
    user = user_factory.create()
    document_factory.create_batch(2, owner=user, is_favorite=True)
    document_factory.create_batch(3, owner=user, is_favorite=False)
    response = client.get(
        f"{settings.API_V1_STR}/documents?is_favorite=true",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["data"]) == 2
    for document in data["data"]:
        assert document["is_favorite"] is True


def test_filter_documents_by_recently_visited(
    client: TestClient, user_factory: UserFactory, document_factory: DocumentFactory
) -> None:
    user = user_factory.create()
    doc1 = document_factory.create(
        owner=user,
        visited_at=datetime.now(UTC) - timedelta(days=3),
        filename="recent1.txt",
    )
    doc2 = document_factory.create(
        owner=user,
        visited_at=datetime.now(UTC) - timedelta(days=5),
        filename="recent2.txt",
    )
    document_factory.create_batch(
        3,
        owner=user,
        visited_at=datetime.now(UTC) - timedelta(days=30),
        filename="old1.txt",
    )
    document_factory.create_batch(2, owner=user, visited_at=None)

    response = client.get(
        f"{settings.API_V1_STR}/documents?recently_visited=true",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert data["count"] == 2
    assert len(data["data"]) == 2
    returned_ids = {doc["id"] for doc in data["data"]}
    assert str(doc1.id) in returned_ids
    assert str(doc2.id) in returned_ids


def test_upload_document(
    client: TestClient, user_factory: UserFactory, tmp_path: Path
) -> None:
    user = user_factory.create()
    file_content = b"Sample document content"
    files = {"file": ("sample.txt", file_content, "text/plain")}
    with (
        patch("documents.domain.services.document.save_document_to_path") as mock_path,
        patch("documents.api.routes.document.chunk_document"),
        patch("documents.api.routes.document.embed_document_chunks"),
    ):
        mock_path.return_value = tmp_path / "20240101_000000"
        response = client.post(
            f"{settings.API_V1_STR}/documents",
            headers=user_authentication_headers(
                client=client, email=user.email, password="password"
            ),
            data={"description": "Test document description"},
            files=files,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "sample.txt"
    assert data["is_processed"] is False


def test_upload_document_with_category(
    client: TestClient, user_factory: UserFactory, tmp_path: Path
) -> None:
    user = user_factory.create()
    file_content = b"Sample document content"
    files = {"file": ("sample.txt", file_content, "text/plain")}
    with (
        patch("documents.domain.services.document.save_document_to_path") as mock_path,
        patch("documents.api.routes.document.chunk_document"),
        patch("documents.api.routes.document.embed_document_chunks"),
    ):
        mock_path.return_value = tmp_path / "20240101_000000"
        response = client.post(
            f"{settings.API_V1_STR}/documents",
            headers=user_authentication_headers(
                client=client, email=user.email, password="password"
            ),
            data={
                "description": "Test document description",
                "category": "marketing",
                "chunk_size": "1024",
            },
            files=files,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "sample.txt"
    assert data["is_processed"] is False
    assert data["category"] == "marketing"


def test_download_document(
    client: TestClient,
    user_factory: UserFactory,
    document_factory: DocumentFactory,
    tmp_path: Path,
) -> None:
    user = user_factory.create()
    document_path = tmp_path / "download_test_document.txt"
    document_path.write_bytes(b"Sample document content for download test")
    document = document_factory.create(owner=user, file_path=str(document_path))
    response = client.get(
        f"{settings.API_V1_STR}/documents/download/{document.id}",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 200
    assert response.content == b"Sample document content for download test"


def test_upload_document_triggers_chunking(
    client: TestClient,
    user_factory: UserFactory,
    tmp_path: Path,
) -> None:
    user = user_factory.create()
    file_content = b"Sample document content for chunking test"
    files = {"file": ("chunk_test.txt", file_content, "text/plain")}
    data_form = {"description": "Chunking test document description"}
    with (
        patch("documents.domain.services.document.save_document_to_path") as mock_path,
        patch("documents.api.routes.document.chunk_document") as mock_chunk_document,
    ):
        mock_path.return_value = tmp_path / "20240101_000000"
        response = client.post(
            f"{settings.API_V1_STR}/documents",
            headers=user_authentication_headers(
                client=client, email=user.email, password="password"
            ),
            files=files,
            json=data_form,
        )

    assert response.status_code == 200
    data = response.json()

    document_id = UUID(data["id"])
    mock_chunk_document.assert_called_once()
    call_kwargs = mock_chunk_document.call_args.kwargs
    assert call_kwargs["document_id"] == document_id
    assert call_kwargs["chunk_size"] == 1024


def test_get_document_stats(
    client: TestClient,
    user_factory: UserFactory,
    document_factory: DocumentFactory,
) -> None:
    user = user_factory.create()
    document_factory.create_batch(2, owner=user, is_archived=True)
    document_factory.create_batch(3, owner=user, is_favorite=True)
    document_factory.create_batch(5, owner=user)
    document_factory.create_batch(5, owner=user, category=DocumentCategory.MARKETING)
    document_factory.create_batch(3, owner=user, category=DocumentCategory.SALES)
    document_factory.create_batch(7, owner=user, category=DocumentCategory.HR)
    response = client.get(
        f"{settings.API_V1_STR}/documents/stats",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] == 25
    assert data["archived_documents"] == 2
    assert data["favorite_documents"] == 3
    # default category is TECHNICAL
    assert data["technical_documents"] == 10
    assert data["marketing_documents"] == 5
    assert data["sales_documents"] == 3
    assert data["hr_documents"] == 7
    assert data["finance_documents"] == 0
    assert data["legal_documents"] == 0
    assert data["product_documents"] == 0


def test_update_document(
    client: TestClient,
    user_factory: UserFactory,
    document_factory: DocumentFactory,
) -> None:
    user = user_factory.create()
    document = document_factory.create(
        owner=user, description="Old description", is_archived=False, is_favorite=False
    )
    update_data = {
        "description": "New description",
        "is_archived": True,
        "is_favorite": True,
        "category": "hr",
    }
    response = client.patch(
        f"{settings.API_V1_STR}/documents/{document.id}",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
        json=update_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "New description"
    assert data["is_archived"] is True
    assert data["is_favorite"] is True
    assert data["category"] == "hr"


def test_delete_document(
    client: TestClient,
    user_factory: UserFactory,
    document_factory: DocumentFactory,
) -> None:
    user = user_factory.create()
    document = document_factory.create(owner=user)
    response = client.delete(
        f"{settings.API_V1_STR}/documents/{document.id}",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 204


def test_get_document_markdown_preview(
    client: TestClient,
    user_factory: UserFactory,
    document_factory: DocumentFactory,
    document_chunk_factory: DocumentChunkFactory,
) -> None:
    user = user_factory.create()
    document = document_factory.create(owner=user)
    document_chunk_factory.create(
        document=document, chunk_index=0, content="This is the first chunk."
    )
    document_chunk_factory.create(
        document=document, chunk_index=1, content="This is the second chunk."
    )
    response = client.get(
        f"{settings.API_V1_STR}/documents/{document.id}/preview/markdown",
        headers=user_authentication_headers(
            client=client, email=user.email, password="password"
        ),
    )
    assert response.status_code == 200
    data = response.json()
    expected_markdown = "This is the first chunk.\nThis is the second chunk."
    assert data == expected_markdown


def test_get_document_predictions(
    client: TestClient,
    user_factory: UserFactory,
    document_factory: DocumentFactory,
    document_chunk_factory: DocumentChunkFactory,
) -> None:
    user = user_factory.create()
    document = document_factory.create(owner=user)
    document_chunk_factory.create(
        document=document, chunk_index=0, content="The capital of France is Paris."
    )
    document_chunk_factory.create(
        document=document, chunk_index=1, content="The capital of Germany is Berlin."
    )
    return_value = [(document, "The capital of France is Paris.", 0.95)]
    client.app.state.embedding_model = MagicMock()  # type: ignore

    with patch(
        "documents.domain.services.document.get_document_predictions",
        return_value=return_value,
    ):
        response = client.post(
            f"{settings.API_V1_STR}/documents/predict",
            headers=user_authentication_headers(
                client=client, email=user.email, password="password"
            ),
            json={"search_query": "What is the capital of France?"},
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data["predictions"]) == 1
    prediction = data["predictions"][0]
    assert prediction["document"]["id"] == str(document.id)
    assert prediction["chunk_content"] == "The capital of France is Paris."
