from fastapi import APIRouter
from pydantic import BaseModel

from core.security import get_password_hash
from users.api.schemas.user import (
    UserPublic,
)
from users.deps import SessionDep
from users.domain.models.user import User as DbUser

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> DbUser:
    """
    Create a new user.
    """

    user = DbUser(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    session.commit()

    return user
