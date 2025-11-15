from faker import Faker
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from core.config import settings
from users.domain.models.user import User


def test_create_user(client: TestClient, db: Session) -> None:
    email = Faker().email()
    full_name = Faker().name()
    r = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={
            "email": email,
            "password": "strongpassword",
            "full_name": full_name,
        },
    )

    assert r.status_code == 200

    data = r.json()

    user = db.exec(select(User).where(User.id == data["id"])).first()

    assert user
    assert user.email == email
    assert user.full_name == full_name
