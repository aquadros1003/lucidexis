from typing import Generic, TypeVar, overload

from factory.alchemy import SQLAlchemyModelFactory

TModel = TypeVar("TModel")


class TypedSQLAFactory(SQLAlchemyModelFactory, Generic[TModel]):
    class Meta:
        sqlalchemy_session_persistence = "commit"

    @overload  # type: ignore[misc]
    @classmethod
    def create(cls: type["TypedSQLAFactory[TModel]"], **kwargs: object) -> TModel: ...

    @classmethod
    def create(cls, **kwargs) -> TModel:  # type: ignore
        """Create and persist an instance of the model this factory creates.

        This method is a thin wrapper around the parent class's `create` method
        that adds type information to make mypy happy.
        """
        return super().create(**kwargs)  # type: ignore[no-any-return]

    @overload  # type: ignore[misc]
    @classmethod
    def build(cls: type["TypedSQLAFactory[TModel]"], **kwargs: object) -> TModel: ...

    @classmethod
    def build(cls, **kwargs) -> TModel:  # type: ignore
        """Build (but do not persist) an instance of the model this factory creates.

        This method is a thin wrapper around the parent class's `build` method
        that adds type information to make mypy happy.
        """
        return super().build(**kwargs)  # type: ignore[no-any-return]
