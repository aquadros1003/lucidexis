from fastapi import APIRouter

from .conversation import conversation_router

router = APIRouter(prefix="/chat", tags=["chat"])
router.include_router(conversation_router)
