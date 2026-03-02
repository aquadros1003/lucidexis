from fastapi import APIRouter

from .chat import websocket_router
from .conversation import conversation_router
from .message import conversation_router as message_router

router = APIRouter(prefix="/chat", tags=["chat"])
router.include_router(conversation_router)
router.include_router(websocket_router)
router.include_router(message_router)
