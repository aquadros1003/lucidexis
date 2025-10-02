from pydantic import EmailStr
from sqlmodel import Field

from core.base_model import SQLModelBase


class User(SQLModelBase, table=True):
    __tablename__ = "user"

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    hashed_password: str

    def __repr__(self) -> str:
        return f"User(email={self.email}, is_active={self.is_active})"

    def __str__(self) -> str:
        return f"User(email={self.email}, is_active={self.is_active})"
