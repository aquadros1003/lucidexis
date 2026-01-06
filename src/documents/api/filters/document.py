from datetime import datetime

from fastapi_filter.contrib.sqlalchemy import Filter

from documents.domain.models.document import Document, DocumentCategory


class DocumentFilter(Filter):
    filename__ilike: str | None = None
    is_archived: bool | None = None
    is_favorite: bool | None = None
    category: DocumentCategory | None = None
    created_at__gte: datetime | None = None
    created_at__lte: datetime | None = None
    order_by: list[str] = ["-created_at"]

    class Constants(Filter.Constants):
        model = Document
