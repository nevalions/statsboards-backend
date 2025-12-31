import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.core.db_session_manager import db_session_context, with_db_session
from src.core.models import SportDB


class TestDBSessionManager:
    async def test_db_session_context_commit_success(self, test_db):
        async with db_session_context(test_db.async_session) as session:
            sport = SportDB(title="Football")
            session.add(sport)

        async with test_db.async_session() as session:
            result = await session.execute(
                select(SportDB).where(SportDB.title == "Football")
            )
            assert result.scalars().one_or_none() is not None

    async def test_db_session_context_rollback_on_sqlalchemy_error(self, test_db):
        with pytest.raises(SQLAlchemyError):
            async with db_session_context(test_db.async_session) as session:
                sport = SportDB(title="Football")
                session.add(sport)
                await session.flush()
                raise SQLAlchemyError("Simulated database error")

        async with test_db.async_session() as session:
            result = await session.execute(
                select(SportDB).where(SportDB.title == "Football")
            )
            assert result.scalars().one_or_none() is None

    async def test_db_session_context_rollback_on_integrity_error(self, test_db):
        with pytest.raises(IntegrityError):
            async with db_session_context(test_db.async_session) as session:
                sport = SportDB(title="Football")
                session.add(sport)
                await session.flush()
                raise IntegrityError("Simulated integrity error", "orig", Exception())

        async with test_db.async_session() as session:
            result = await session.execute(
                select(SportDB).where(SportDB.title == "Football")
            )
            assert result.scalars().one_or_none() is None

    async def test_db_session_context_rollback_on_generic_exception(self, test_db):
        with pytest.raises(ValueError):
            async with db_session_context(test_db.async_session) as session:
                sport = SportDB(title="Football")
                session.add(sport)
                await session.flush()
                raise ValueError("Simulated generic error")

        async with test_db.async_session() as session:
            result = await session.execute(
                select(SportDB).where(SportDB.title == "Football")
            )
            assert result.scalars().one_or_none() is None


class TestWithDBSessionDecorator:
    async def test_with_db_session_decorator_success(self, test_db):
        class TestService:
            def __init__(self, db):
                self.db = db

            @with_db_session()
            async def create_sport(self, session, title):
                sport = SportDB(title=title)
                session.add(sport)
                return sport

        service = TestService(test_db)
        sport = await service.create_sport("Basketball")

        assert sport is not None
        async with test_db.async_session() as session:
            result = await session.execute(
                select(SportDB).where(SportDB.title == "Basketball")
            )
            assert result.scalars().one_or_none() is not None

    async def test_with_db_session_decorator_rollback_on_error(self, test_db):
        class TestService:
            def __init__(self, db):
                self.db = db

            @with_db_session()
            async def create_sport_with_error(self, session, title):
                sport = SportDB(title=title)
                session.add(sport)
                await session.flush()
                raise ValueError("Simulated error")

        service = TestService(test_db)

        with pytest.raises(ValueError):
            await service.create_sport_with_error("Tennis")

        async with test_db.async_session() as session:
            result = await session.execute(
                select(SportDB).where(SportDB.title == "Tennis")
            )
            assert result.scalars().one_or_none() is None

    async def test_with_db_session_decorator_with_custom_db_property(self, test_db):
        class TestService:
            def __init__(self, database):
                self.custom_db = database

            @with_db_session("custom_db")
            async def create_sport(self, session, title):
                sport = SportDB(title=title)
                session.add(sport)
                return sport

        service = TestService(test_db)
        sport = await service.create_sport("Volleyball")

        assert sport is not None
        async with test_db.async_session() as session:
            result = await session.execute(
                select(SportDB).where(SportDB.title == "Volleyball")
            )
            assert result.scalars().one_or_none() is not None
