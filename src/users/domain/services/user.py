from sqlmodel import Session, select

from core.security import get_password_hash, verify_password
from users.api.schemas.user import UserUpdate
from users.domain.models.user import User as DbUser


def create_user(
    *,
    session: Session,
    email: str,
    password: str,
    full_name: str | None = None,
    is_active: bool = True,
    is_superuser: bool = False,
    locale: str = "pl_PL",
) -> DbUser:
    db_obj = DbUser.model_validate(
        {
            "email": email,
            "is_active": is_active,
            "hashed_password": get_password_hash(password),
            "full_name": full_name,
            "is_superuser": is_superuser,
            "locale": locale,
        }
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: DbUser, user_in: UserUpdate) -> DbUser:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> DbUser | None:
    statement = select(DbUser).where(DbUser.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> DbUser | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def update_user_model_preferences(
    *,
    session: Session,
    db_user: DbUser,
    llm_model: str | None = None,
    openai_api_url: str | None = None,
    openai_api_key: str | None = None,
    openai_system_prompt: str | None = None,
) -> DbUser:
    update_data = {}
    update_data["llm_model"] = llm_model
    update_data["openai_api_url"] = openai_api_url
    update_data["openai_api_key"] = openai_api_key
    update_data["openai_system_prompt"] = openai_system_prompt
    db_user.sqlmodel_update(update_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
