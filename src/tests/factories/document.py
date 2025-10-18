# import factory
# from pytest_factoryboy import register


# from tests.factories.base import TypedSQLAFactory
# from documents.domain.models.document import Document
# from tests.factories.user import UserFactory


# @register
# class UserFactory(TypedSQLAFactory["Document"]):
#     class Meta:
#         model = Document
#         sqlalchemy_session_persistence = "commit"

#     filename = factory.Faker("file_name", extension="pdf")
#     content_type = "application/pdf"
#     owner = factory.SubFactory(UserFactory)
