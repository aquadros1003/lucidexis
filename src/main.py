import logging.config
import tomllib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute
from sentence_transformers import SentenceTransformer
from starlette.middleware.cors import CORSMiddleware

from chat.api.routes import router as chat_router
from core.config import settings
from documents.api.routes.document import router as document_router
from users.api.routes.login import router as login_router
from users.api.routes.private import router as private_router
from users.api.routes.users import router as users_router


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


logging.config.dictConfig(settings.LOGGING_CONFIG)


def get_version() -> str:
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if not pyproject.is_file():
        return "0.1.0"
    data = tomllib.loads(pyproject.read_text("utf-8"))
    if "project" in data and "version" in data["project"]:
        return data["project"]["version"]
    return "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    app.state.embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=get_version(),
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(login_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(document_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
if settings.ENVIRONMENT == "local":
    app.include_router(private_router, prefix=settings.API_V1_STR)
