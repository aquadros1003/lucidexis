import factory
from pytest_factoryboy import register

from core.security import get_password_hash
from users.domain.models.user import User


@register
class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    email = factory.Faker("email")
    hashed_password = factory.LazyFunction(lambda: get_password_hash("password"))
    is_active = True
    is_superuser = False
    full_name = factory.Faker("name")
