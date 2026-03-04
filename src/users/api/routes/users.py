import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

import users.domain.services.user as user_service
from core.config import settings
from core.db import SessionDep
from core.security import get_password_hash, verify_password
from users.api.schemas.user import (
    Message,
    UpdatePassword,
    UpdateUserModelPreferences,
    UserCreate,
    UserModelPreferencesResponse,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from users.deps import CurrentUser, get_current_active_superuser
from users.domain.models.user import User as DbUser
from users.domain.services.user import (
    update_user_model_preferences as update_user_model_preferences_service,
)
from utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
async def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(DbUser)
    count = session.exec(count_statement).one()

    statement = select(DbUser).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=[UserPublic.model_validate(u) for u in users], count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
async def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = user_service.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = user_service.create_user(session=session, **user_in.model_dump())
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
async def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
async def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
async def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = user_service.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = user_service.create_user(session=session, **user_create.model_dump())
    return user


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(DbUser, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(DbUser, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = user_service.get_user_by_email(
            session=session, email=user_in.email
        )
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = user_service.update_user(
        session=session, db_user=db_user, user_in=user_in
    )
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
async def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = session.get(DbUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")


@router.get("/me/model-preferences", response_model=UserModelPreferencesResponse)
async def get_user_model_preferences(
    current_user: CurrentUser,
) -> Any:
    """
    Get current user's LLM model preferences.
    """
    print(
        current_user.llm_model,
        current_user.openai_api_url,
        current_user.openai_api_key,
        current_user.openai_system_prompt,
    )
    return UserModelPreferencesResponse(
        llm_model=current_user.llm_model,
        openai_api_url=current_user.openai_api_url,
        openai_api_key=current_user.openai_api_key,
        openai_system_prompt=current_user.openai_system_prompt,
    )


@router.patch("/me/model-preferences", response_model=UserModelPreferencesResponse)
async def update_user_model_preferences(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    preferences_in: UpdateUserModelPreferences,
) -> Any:
    db_user = update_user_model_preferences_service(
        session=session,
        db_user=current_user,
        llm_model=preferences_in.llm_model,
        openai_api_url=preferences_in.openai_api_url,
        openai_api_key=preferences_in.openai_api_key,
        openai_system_prompt=preferences_in.openai_system_prompt,
    )
    return UserModelPreferencesResponse(
        llm_model=db_user.llm_model,
        openai_api_url=db_user.openai_api_url,
        openai_api_key=db_user.openai_api_key,
        openai_system_prompt=db_user.openai_system_prompt,
    )
