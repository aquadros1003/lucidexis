from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class ConversationPublic(SQLModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class LatestConversationResponse(SQLModel):
    conversation: ConversationPublic


class StartConversationResponse(SQLModel):
    conversation: ConversationPublic
