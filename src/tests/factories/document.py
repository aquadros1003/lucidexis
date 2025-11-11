import factory
from pytest_factoryboy import register

from documents.domain.models.document import Document
from tests.factories.base import TypedSQLAFactory
from tests.factories.user import UserFactory


@register
class DocumentFactory(TypedSQLAFactory["Document"]):
    class Meta:
        model = Document
        sqlalchemy_session_persistence = "commit"

    filename = factory.Faker("file_name", extension="pdf")
    content_type = "application/pdf"
    file_path = factory.Sequence(lambda n: f"/tmp/fake_path/document_{n}.pdf")
    file_size = factory.Faker("random_int", min=1000, max=1000000)
    owner = factory.SubFactory(UserFactory)
    description = factory.Faker("sentence", nb_words=6)
