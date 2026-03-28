import argparse
import logging
import mimetypes
import os
import random
import shutil
from pathlib import Path
from uuid import uuid4

import factory
import transformers
from rich.console import Console
from rich.progress import track
from rich.prompt import IntPrompt
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import sessionmaker
from transformers.utils.logging import disable_progress_bar

from core.config import settings
from core.db import engine
from core.security import get_password_hash
from documents.domain.models.document import Document, DocumentCategory
from documents.domain.services.chunk import chunk_document, embed_document_chunks
from tests.factories.base import TypedSQLAFactory
from users.domain.models.user import User

logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
transformers.logging.set_verbosity_error()
disable_progress_bar()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()
console = Console()


class UserFactory(TypedSQLAFactory["User"]):
    class Meta:
        model = User
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    email = factory.Sequence(lambda n: f"lucidexis{n}@lucidexis.app")
    hashed_password = factory.LazyFunction(lambda: get_password_hash("lucidexis"))
    is_active = True
    is_superuser = False
    full_name = factory.Sequence(lambda n: f"Lucidexis {n}")
    locale = "pl_PL"
    llm_model = os.getenv("DEFAULT_LLM_MODEL")
    openai_api_url = os.getenv("DEFAULT_OPENAI_API_URL")
    openai_api_key = os.getenv("DEFAULT_OPENAI_API_KEY")


def load_user_docs(users: list[User]) -> int:
    embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
    base_dir = Path(__file__).resolve().parent
    mock_documents_dir = base_dir / "mocks" / "documents"
    source_files = [
        path for path in sorted(mock_documents_dir.iterdir()) if path.is_file()
    ]
    if not users or not source_files:
        return 0
    created_docs = 0
    for source_file in track(source_files, description="Processing mock documents..."):
        dest_dir = Path(settings.DOCUMENTS_DIR)
        dest_file = dest_dir / f"{uuid4()}_{source_file.name}"
        shutil.copy(source_file, dest_file)
        content_type, _ = mimetypes.guess_type(dest_file)
        if not content_type:
            continue
        for user in users:
            document = Document.model_validate(
                {
                    "owner_id": user.id,
                    "file_path": str(dest_file),
                    "content_type": content_type,
                    "filename": source_file.name.replace("_", " ").capitalize(),
                    "file_size": dest_file.stat().st_size,
                    "category": random.choice(list(DocumentCategory)),
                }
            )
            if document_exists_for_user(user, document.filename):
                continue
            session.add(document)
            session.commit()
            chunk_document(document_id=document.id, chunk_size=500, session=session)
            description = (
                document.chunks[0].content[:100] + "..." if document.chunks else ""
            )
            document.description = description
            session.add(document)
            session.commit()
            embed_document_chunks(
                document_id=document.id,
                session=session,
                embedding_model=embedding_model,
            )
            created_docs += 1
    return created_docs


def get_user_by_email(email: str) -> User | None:
    return session.query(User).filter_by(email=email).first()


def document_exists_for_user(user: User, filename: str) -> bool:
    return (
        session.query(Document).filter_by(owner_id=user.id, filename=filename).first()
        is not None
    )


def generate_test_users(start_index: int = 0, num_users: int = 10) -> tuple[int, int]:
    users = []
    created_users = 0
    indices = range(start_index, start_index + num_users)
    for n in track(indices, description="Creating/checking users..."):
        email = f"lucidexis{n}@lucidexis.app"
        user = get_user_by_email(email)
        if not user:
            user = UserFactory.create(email=email)
            created_users += 1
        users.append(user)
    created_docs = load_user_docs(users)
    return created_users, created_docs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate test users and attach mock documents.",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        help="Starting index for generated emails (e.g., 0).",
    )
    parser.add_argument(
        "--num-users",
        type=int,
        default=10,
        help="Number of users to create/check (default: 10).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    start_index = (
        args.start_index
        if args.start_index is not None
        else IntPrompt.ask("Enter starting index for test users", default=0)
    )
    num_users = args.num_users

    if start_index < 0:
        parser.error("--start-index must be >= 0")
    if num_users <= 0:
        parser.error("--num-users must be > 0")

    console.print(
        f"[bold cyan]Generating test users[/] | start_index={start_index}, "
        f"num_users={num_users}"
    )

    created_users, created_docs = generate_test_users(
        start_index=start_index,
        num_users=num_users,
    )

    console.print(
        "[bold green]Done[/] "
        f"Created [bold]{created_users}[/] new users (checked {num_users}) and "
        f"attached [bold]{created_docs}[/] documents from scripts/mocks/documents."
    )


if __name__ == "__main__":
    main()
