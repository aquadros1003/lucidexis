from uuid import UUID

from pydantic import BaseModel

from chat.domain.models.message import MessageRole


class MessageCreate(BaseModel):
    content: str
    conversation_id: UUID


class MessagesPublic(BaseModel):
    messages: list["MessagePublic"]


class MessagePublic(BaseModel):
    id: UUID
    content: str
    role: MessageRole
    conversation_id: UUID
    additional_data: dict | None = None


class MessageResponse(BaseModel):
    type: str = "message"
    message: MessagePublic


class ErrorResponse(BaseModel):
    type: str = "error"
    error: str
