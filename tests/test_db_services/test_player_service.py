import pytest
from fastapi import HTTPException

from src.core.models.base import Database
from src.player.db_services import PlayerServiceDB
from src.player.schemas import PlayerSchemaCreate, PlayerSchemaUpdate
from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaCreate
from src.sports.db_services import SportServiceDB
from src.sports.schemas import SportSchemaCreate
from tests.factories import PlayerFactory, PersonFactory, SportFactorySample
from src.logging_config import setup_logging

setup_logging()


@pytest.fixture(scope="function")
def sport(test_db: Database):
    return SportFactorySample.build()


@pytest.fixture(scope="function")
def person(test_db: Database):
    person_data = PersonFactory.build(person_eesl_id=999, first_name="Test")
    return person_data


@pytest.mark.asyncio
class TestPlayerServiceDBCreateOrUpdate:
    """Test create_or_update_player functionality."""

    async def test_create_player_with_eesl_id(
        self, test_db: Database, sport: SportSchemaCreate, person: PersonSchemaCreate
    ):
        """Test creating a player with eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create_sport(sport)

        person_service = PersonServiceDB(test_db)
        created_person = await person_service.create_or_update_person(person)

        player_service = PlayerServiceDB(test_db)
        player_data = PlayerFactory.build(
            sport_id=created_sport.id,
            person_id=created_person.id,
            player_eesl_id=100,
        )

        result = await player_service.create_or_update_player(player_data)

        assert result is not None
        assert result.id is not None
        assert result.player_eesl_id == 100
        assert result.person_id == created_person.id

    async def test_create_player_without_eesl_id(
        self, test_db: Database, sport: SportSchemaCreate, person: PersonSchemaCreate
    ):
        """Test creating a player without eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create_sport(sport)

        person_service = PersonServiceDB(test_db)
        created_person = await person_service.create_or_update_person(person)

        player_service = PlayerServiceDB(test_db)
        player_data = PlayerFactory.build(
            sport_id=created_sport.id, person_id=created_person.id, player_eesl_id=None
        )

        result = await player_service.create_or_update_player(player_data)

        assert result is not None
        assert result.id is not None
        assert result.player_eesl_id is None

    async def test_update_existing_player_by_eesl_id(
        self, test_db: Database, sport: SportSchemaCreate, person: PersonSchemaCreate
    ):
        """Test updating an existing player by eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create_sport(sport)

        person_service = PersonServiceDB(test_db)
        created_person = await person_service.create_or_update_person(person)

        player_service = PlayerServiceDB(test_db)

        player_data = PlayerFactory.build(
            sport_id=created_sport.id, person_id=created_person.id, player_eesl_id=200
        )
        created = await player_service.create_or_update_player(player_data)

        update_data = PlayerSchemaUpdate(player_eesl_id=200)

        updated = await player_service.create_or_update_player(update_data)

        assert updated.id == created.id

    async def test_create_multiple_players(
        self, test_db: Database, sport: SportSchemaCreate, person: PersonSchemaCreate
    ):
        """Test creating multiple players."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create_sport(sport)

        person_service = PersonServiceDB(test_db)
        created_person = await person_service.create_or_update_person(person)

        player_service = PlayerServiceDB(test_db)

        player1_data = PlayerFactory.build(
            sport_id=created_sport.id, person_id=created_person.id, player_eesl_id=301
        )
        player2_data = PlayerFactory.build(
            sport_id=created_sport.id, person_id=created_person.id, player_eesl_id=302
        )

        player1 = await player_service.create_or_update_player(player1_data)
        player2 = await player_service.create_or_update_player(player2_data)

        assert player1.player_eesl_id == 301
        assert player2.player_eesl_id == 302
        assert player1.id != player2.id

    async def test_get_player_by_eesl_id(
        self, test_db: Database, sport: SportSchemaCreate, person: PersonSchemaCreate
    ):
        """Test retrieving player by eesl_id."""
        sport_service = SportServiceDB(test_db)
        created_sport = await sport_service.create_sport(sport)

        person_service = PersonServiceDB(test_db)
        created_person = await person_service.create_or_update_person(person)

        player_service = PlayerServiceDB(test_db)

        player_data = PlayerFactory.build(
            sport_id=created_sport.id, person_id=created_person.id, player_eesl_id=400
        )
        created = await player_service.create_or_update_player(player_data)

        retrieved = await player_service.get_player_by_eesl_id(400)

        assert retrieved is not None
        assert retrieved.id == created.id
