from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient

from core.config import settings
from tests.factories.document import DocumentFactory
from tests.factories.user import UserFactory
from tests.utils.user import user_authentication_headers


def test_upload_document(
    client: TestClient, user_factory: UserFactory, tmp_path: Path
) -> None:
    user = user_factory.create()
    file_content = b"Sample document content"
    files = {"file": ("sample.txt", file_content, "text/plain")}
    with patch("documents.domain.services.document.save_document_to_path") as mock_path:
        mock_path.return_value = tmp_path / "20240101_000000"
        response = client.post(
            f"{settings.API_V1_STR}/documents",
            headers=user_authentication_headers(
                client=client, email=user.email, password="password"
            ),
            files=files,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "sample.txt"
    assert data["is_processed"] is False


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
        f"{settings.API_V1_STR}/documents/{document.id}",
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
        )

    assert response.status_code == 200
    data = response.json()

    document_id = UUID(data["id"])
    mock_chunk_document.assert_called_once()
    call_kwargs = mock_chunk_document.call_args.kwargs
    assert call_kwargs["document_id"] == document_id
    assert call_kwargs["chunk_size"] == 1024
