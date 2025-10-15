from sqlmodel import Session

from documents.domain.models.document import Document as DbDocument


def add_document(
    *, session: Session, owner_id: str, filename: str, content_type: str
) -> DbDocument:
    db_obj = DbDocument.model_validate(
        {
            "filename": filename,
            "content_type": content_type,
            "owner_id": owner_id,
        }
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj
