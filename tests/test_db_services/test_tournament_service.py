import pytest
from fastapi import HTTPException

from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaCreate as PersonSchemaCreateType
from src.player.db_services import PlayerServiceDB
from src.player.schemas import PlayerSchemaCreate as PlayerSchemaCreateType
from src.seasons.schemas import SeasonSchemaCreate
from src.sports.schemas import SportSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.teams.schemas import TeamSchemaCreate as TeamSchemaCreateType
from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import TournamentSchemaCreate
from tests.factories import TournamentFactory
from tests.testhelpers import (
    assert_http_exception_on_create,
    assert_tournament_equal,
)


@pytest.fixture(scope="function")
def tournament_sample(sport, season) -> TournamentSchemaCreate:
    return TournamentFactory.build(
        sport_id=sport.id,
        season_id=season.id,
    )


@pytest.mark.asyncio
class TestTournamentServiceDB:
    async def test_create_tournament_with_relations(
        self,
        test_tournament_service: TournamentServiceDB,
        season,
        sport,
        tournament_sample: TournamentSchemaCreate,
    ):
        """Test creating a tournament with related sport and season."""
        created_tournament: TournamentSchemaCreate = await test_tournament_service.create(
            tournament_sample
        )
        assert created_tournament.season_id == season.id
        assert created_tournament.sport_id == sport.id
        assert created_tournament.title == tournament_sample.title
        assert created_tournament.description == tournament_sample.description

    async def test_create_tournament_without_sport_id(
        self,
        test_tournament_service: TournamentServiceDB,
        tournament_sample: TournamentSchemaCreate,
    ):
        """Test that a tournament cannot be created without a sport_id."""
        from src.tournaments.schemas import TournamentSchemaCreate

        invalid_tournament_sample = TournamentSchemaCreate.model_construct(
            sport_id=None,
            season_id=tournament_sample.season_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await test_tournament_service.create(invalid_tournament_sample)

        assert_http_exception_on_create(exc_info)

    async def test_create_tournament_without_season_id(
        self,
        test_tournament_service: TournamentServiceDB,
        tournament_sample: TournamentSchemaCreate,
    ):
        """Test that a tournament cannot be created without a season_id."""
        invalid_tournament_sample = TournamentSchemaCreate.model_construct(
            sport_id=tournament_sample.sport_id,
            season_id=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await test_tournament_service.create(invalid_tournament_sample)

        assert_http_exception_on_create(exc_info)

    async def test_create_tournament_without_the_same_eesl_id(
        self,
        test_tournament_service: TournamentServiceDB,
        tournament_sample: TournamentSchemaCreate,
    ):
        """Test that a tournament cannot be created with same tournament_eesl_id."""
        invalid_tournament_sample = TournamentSchemaCreate.model_construct(
            tournament_eesl_id=tournament_sample.tournament_eesl_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await test_tournament_service.create(invalid_tournament_sample)

        assert_http_exception_on_create(exc_info)

    async def test_get_tournament_with_eesl_id(
        self,
        test_tournament_service: TournamentServiceDB,
        tournament: TournamentSchemaCreate,
        season: SeasonSchemaCreate,
        sport: SportSchemaCreate,
    ):
        """Test that a tournament can be retrieved using its eesl_id."""
        retrieved_tournament = await test_tournament_service.get_tournament_by_eesl_id(
            tournament.tournament_eesl_id
        )
        assert_tournament_equal(tournament, retrieved_tournament, season, sport)

    async def test_get_teams_by_tournament_with_pagination(
        self,
        test_tournament_service: TournamentServiceDB,
        test_team_service: TeamServiceDB,
        tournament,
        sport,
    ):
        """Test retrieving teams in tournament with pagination and search."""
        from src.core.models.team_tournament import TeamTournamentDB

        team1 = TeamSchemaCreateType(
            title="Manchester United",
            sport_id=sport.id,
            team_eesl_id=1001,
        )
        team1_db = await test_team_service.create_or_update_team(team1)

        team2 = TeamSchemaCreateType(
            title="Manchester City",
            sport_id=sport.id,
            team_eesl_id=1002,
        )
        team2_db = await test_team_service.create_or_update_team(team2)

        team3 = TeamSchemaCreateType(
            title="Liverpool",
            sport_id=sport.id,
            team_eesl_id=1003,
        )
        team3_db = await test_team_service.create_or_update_team(team3)

        async with test_tournament_service.db.async_session() as session:
            tt1 = TeamTournamentDB(tournament_id=tournament.id, team_id=team1_db.id)
            tt2 = TeamTournamentDB(tournament_id=tournament.id, team_id=team2_db.id)
            tt3 = TeamTournamentDB(tournament_id=tournament.id, team_id=team3_db.id)
            session.add_all([tt1, tt2, tt3])
            await session.flush()

        result = await test_tournament_service.get_teams_by_tournament_with_pagination(
            tournament_id=tournament.id,
            skip=0,
            limit=20,
        )

        assert result.metadata.total_items == 3
        assert len(result.data) == 3
        assert result.metadata.page == 1
        assert result.metadata.items_per_page == 20
        assert result.metadata.total_pages == 1

    async def test_get_teams_by_tournament_with_search(
        self,
        test_tournament_service: TournamentServiceDB,
        test_team_service: TeamServiceDB,
        tournament,
        sport,
    ):
        """Test searching teams in tournament by title."""
        from src.core.models.team_tournament import TeamTournamentDB

        team1 = TeamSchemaCreateType(
            title="Manchester United",
            sport_id=sport.id,
            team_eesl_id=1001,
        )
        team1_db = await test_team_service.create_or_update_team(team1)

        team2 = TeamSchemaCreateType(
            title="Manchester City",
            sport_id=sport.id,
            team_eesl_id=1002,
        )
        team2_db = await test_team_service.create_or_update_team(team2)

        team3 = TeamSchemaCreateType(
            title="Liverpool",
            sport_id=sport.id,
            team_eesl_id=1003,
        )
        team3_db = await test_team_service.create_or_update_team(team3)

        async with test_tournament_service.db.async_session() as session:
            tt1 = TeamTournamentDB(tournament_id=tournament.id, team_id=team1_db.id)
            tt2 = TeamTournamentDB(tournament_id=tournament.id, team_id=team2_db.id)
            tt3 = TeamTournamentDB(tournament_id=tournament.id, team_id=team3_db.id)
            session.add_all([tt1, tt2, tt3])
            await session.flush()

        result = await test_tournament_service.get_teams_by_tournament_with_pagination(
            tournament_id=tournament.id,
            search_query="Manchester",
            skip=0,
            limit=20,
        )

        assert result.metadata.total_items == 2
        assert len(result.data) == 2
        team_titles = [team.title for team in result.data]
        assert "Manchester United" in team_titles
        assert "Manchester City" in team_titles
        assert "Liverpool" not in team_titles

    async def test_get_teams_by_tournament_with_pagination_page_2(
        self,
        test_tournament_service: TournamentServiceDB,
        test_team_service: TeamServiceDB,
        tournament,
        sport,
    ):
        """Test pagination on teams in tournament (page 2)."""
        from src.core.models.team_tournament import TeamTournamentDB

        teams_db = []
        for i in range(5):
            team_data = TeamSchemaCreateType(
                title=f"Team {i}",
                sport_id=sport.id,
                team_eesl_id=2000 + i,
            )
            team_db = await test_team_service.create_or_update_team(team_data)
            teams_db.append(team_db)

        async with test_tournament_service.db.async_session() as session:
            tt_entries = [
                TeamTournamentDB(tournament_id=tournament.id, team_id=team.id) for team in teams_db
            ]
            session.add_all(tt_entries)
            await session.flush()

        result = await test_tournament_service.get_teams_by_tournament_with_pagination(
            tournament_id=tournament.id,
            skip=2,
            limit=2,
        )

        assert result.metadata.total_items == 5
        assert len(result.data) == 2
        assert result.metadata.page == 2
        assert result.metadata.has_next is True
        assert result.metadata.has_previous is True


@pytest.mark.asyncio
class TestTournamentServiceDBPlayersWithoutTeam:
    """Test get_players_without_team_in_tournament functionality."""

    async def test_get_players_without_team_in_tournament_filters_correctly(
        self,
        test_tournament_service: TournamentServiceDB,
        test_team_service: TeamServiceDB,
        tournament,
        sport,
    ):
        """Test filtering players in tournament who are not connected to any team."""
        person_service = PersonServiceDB(test_tournament_service.db)
        player_service = PlayerServiceDB(test_tournament_service.db)

        person1 = await person_service.create(
            PersonSchemaCreateType(first_name="Alice", second_name="TeamPlayer")
        )
        player1 = await player_service.create(
            PlayerSchemaCreateType(sport_id=sport.id, person_id=person1.id, player_eesl_id=9001)
        )

        person2 = await person_service.create(
            PersonSchemaCreateType(first_name="Bob", second_name="NoTeam")
        )
        player2 = await player_service.create(
            PlayerSchemaCreateType(sport_id=sport.id, person_id=person2.id, player_eesl_id=9002)
        )

        person3 = await person_service.create(
            PersonSchemaCreateType(first_name="Charlie", second_name="TeamPlayer2")
        )
        player3 = await player_service.create(
            PlayerSchemaCreateType(sport_id=sport.id, person_id=person3.id, player_eesl_id=9003)
        )

        team_db = await test_team_service.create_or_update_team(
            TeamSchemaCreateType(title="Test Team", sport_id=sport.id, team_eesl_id=5000)
        )

        from src.core.models.player_team_tournament import PlayerTeamTournamentDB

        async with test_tournament_service.db.async_session() as session:
            ptt1 = PlayerTeamTournamentDB(
                player_id=player1.id, tournament_id=tournament.id, team_id=team_db.id
            )
            ptt2 = PlayerTeamTournamentDB(
                player_id=player2.id, tournament_id=tournament.id, team_id=None
            )
            ptt3 = PlayerTeamTournamentDB(
                player_id=player3.id, tournament_id=tournament.id, team_id=team_db.id
            )
            session.add_all([ptt1, ptt2, ptt3])
            await session.flush()

        result = await test_tournament_service.get_players_without_team_in_tournament(
            tournament_id=tournament.id, skip=0, limit=10
        )

        assert len(result.data) == 1
        assert result.data[0].first_name == "Bob"
        assert result.data[0].second_name == "NoTeam"
        assert result.metadata.total_items == 1

    async def test_get_players_without_team_in_tournament_with_search(
        self,
        test_tournament_service: TournamentServiceDB,
        test_team_service: TeamServiceDB,
        tournament,
        sport,
    ):
        """Test search functionality works with team filtering."""
        person_service = PersonServiceDB(test_tournament_service.db)
        player_service = PlayerServiceDB(test_tournament_service.db)

        person1 = await person_service.create(
            PersonSchemaCreateType(first_name="Alice", second_name="NoTeam")
        )
        player1 = await player_service.create(
            PlayerSchemaCreateType(sport_id=sport.id, person_id=person1.id, player_eesl_id=9011)
        )

        person2 = await person_service.create(
            PersonSchemaCreateType(first_name="Alice", second_name="HasTeam")
        )
        player2 = await player_service.create(
            PlayerSchemaCreateType(sport_id=sport.id, person_id=person2.id, player_eesl_id=9012)
        )

        person3 = await person_service.create(
            PersonSchemaCreateType(first_name="Bob", second_name="NoTeam")
        )
        player3 = await player_service.create(
            PlayerSchemaCreateType(sport_id=sport.id, person_id=person3.id, player_eesl_id=9013)
        )

        team_db = await test_team_service.create_or_update_team(
            TeamSchemaCreateType(title="Test Team", sport_id=sport.id, team_eesl_id=5001)
        )

        from src.core.models.player_team_tournament import PlayerTeamTournamentDB

        async with test_tournament_service.db.async_session() as session:
            ptt1 = PlayerTeamTournamentDB(
                player_id=player1.id, tournament_id=tournament.id, team_id=None
            )
            ptt2 = PlayerTeamTournamentDB(
                player_id=player2.id, tournament_id=tournament.id, team_id=team_db.id
            )
            ptt3 = PlayerTeamTournamentDB(
                player_id=player3.id, tournament_id=tournament.id, team_id=None
            )
            session.add_all([ptt1, ptt2, ptt3])
            await session.flush()

        result = await test_tournament_service.get_players_without_team_in_tournament(
            tournament_id=tournament.id, search_query="Alice", skip=0, limit=10
        )

        assert len(result.data) == 1
        assert result.data[0].first_name == "Alice"
        assert result.data[0].second_name == "NoTeam"
        assert result.metadata.total_items == 1

    async def test_get_players_without_team_in_tournament_pagination(
        self, test_tournament_service: TournamentServiceDB, tournament, sport
    ):
        """Test pagination functionality."""
        person_service = PersonServiceDB(test_tournament_service.db)
        player_service = PlayerServiceDB(test_tournament_service.db)

        players = []
        for i in range(5):
            person = await person_service.create(
                PersonSchemaCreateType(first_name=f"Player{i}", second_name="NoTeam")
            )
            player = await player_service.create(
                PlayerSchemaCreateType(
                    sport_id=sport.id, person_id=person.id, player_eesl_id=9500 + i
                )
            )
            players.append(player)

        from src.core.models.player_team_tournament import PlayerTeamTournamentDB

        async with test_tournament_service.db.async_session() as session:
            ptt_entries = [
                PlayerTeamTournamentDB(
                    player_id=player.id, tournament_id=tournament.id, team_id=None
                )
                for player in players
            ]
            session.add_all(ptt_entries)
            await session.flush()

        result = await test_tournament_service.get_players_without_team_in_tournament(
            tournament_id=tournament.id, skip=2, limit=2
        )

        assert result.metadata.total_items == 5
        assert len(result.data) == 2
        assert result.metadata.page == 2
        assert result.metadata.has_next is True
        assert result.metadata.has_previous is True
