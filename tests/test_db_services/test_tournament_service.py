import pytest
from fastapi import HTTPException

from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate
from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaCreate as PersonSchemaCreateType
from src.player.db_services import PlayerServiceDB
from src.player.schemas import PlayerSchemaCreate as PlayerSchemaCreateType
from src.positions.db_services import PositionServiceDB
from src.positions.schemas import PositionSchemaCreate
from src.seasons.db_services import SeasonServiceDB
from src.seasons.schemas import SeasonSchemaCreate
from src.sports.db_services import SportServiceDB
from src.sports.schemas import SportSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.teams.schemas import TeamSchemaCreate as TeamSchemaCreateType
from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import TournamentSchemaCreate
from tests.factories import (
    SeasonFactorySample,
    SportFactoryAny,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)
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

        async with test_tournament_service.db.get_session_maker()() as session:
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

        async with test_tournament_service.db.get_session_maker()() as session:
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

        async with test_tournament_service.db.get_session_maker()() as session:
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

        async with test_tournament_service.db.get_session_maker()() as session:
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

        async with test_tournament_service.db.get_session_maker()() as session:
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

        async with test_tournament_service.db.get_session_maker()() as session:
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


@pytest.mark.asyncio
class TestTournamentServiceDBMoveSport:
    async def test_move_tournament_to_sport_updates_relations_and_positions(self, test_db):
        sport_service = SportServiceDB(test_db)
        source_sport = await sport_service.create(SportFactorySample.build())
        target_sport = await sport_service.create(SportFactoryAny.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team1 = await team_service.create_or_update_team(
            TeamFactory.build(sport_id=source_sport.id, team_eesl_id=3001, title="Team A")
        )
        team2 = await team_service.create_or_update_team(
            TeamFactory.build(sport_id=source_sport.id, team_eesl_id=3002, title="Team B")
        )

        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        person1 = await person_service.create(
            PersonSchemaCreateType(first_name="Alex", second_name="Forward")
        )
        person2 = await person_service.create(
            PersonSchemaCreateType(first_name="Blake", second_name="Goalie")
        )
        player1 = await player_service.create(
            PlayerSchemaCreateType(
                sport_id=source_sport.id, person_id=person1.id, player_eesl_id=9001
            )
        )
        player2 = await player_service.create(
            PlayerSchemaCreateType(
                sport_id=source_sport.id, person_id=person2.id, player_eesl_id=9002
            )
        )

        position_service = PositionServiceDB(test_db)
        source_forward = await position_service.create(
            PositionSchemaCreate(title="Forward", sport_id=source_sport.id)
        )
        source_goalie = await position_service.create(
            PositionSchemaCreate(title="Goalie", sport_id=source_sport.id)
        )
        target_forward = await position_service.create(
            PositionSchemaCreate(title="Forward", sport_id=target_sport.id)
        )

        from src.core.models.player_match import PlayerMatchDB
        from src.core.models.player_team_tournament import PlayerTeamTournamentDB
        from src.core.models.team_tournament import TeamTournamentDB

        async with test_db.get_session_maker()() as session:
            session.add_all(
                [
                    TeamTournamentDB(tournament_id=tournament.id, team_id=team1.id),
                    TeamTournamentDB(tournament_id=tournament.id, team_id=team2.id),
                ]
            )
            await session.flush()

            ptt_forward = PlayerTeamTournamentDB(
                player_id=player1.id,
                team_id=team1.id,
                tournament_id=tournament.id,
                position_id=source_forward.id,
            )
            ptt_goalie = PlayerTeamTournamentDB(
                player_id=player2.id,
                team_id=team1.id,
                tournament_id=tournament.id,
                position_id=source_goalie.id,
            )
            session.add_all([ptt_forward, ptt_goalie])
            await session.flush()

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchSchemaCreate(
                team_a_id=team1.id,
                team_b_id=team2.id,
                tournament_id=tournament.id,
            )
        )

        async with test_db.get_session_maker()() as session:
            player_match = PlayerMatchDB(
                player_team_tournament_id=ptt_goalie.id,
                match_id=match.id,
                team_id=team1.id,
                match_position_id=source_goalie.id,
            )
            session.add(player_match)
            await session.flush()

        result = await tournament_service.move_tournament_to_sport(
            tournament_id=tournament.id,
            target_sport_id=target_sport.id,
        )

        assert result.moved is True
        assert result.updated_counts.tournament == 1
        assert result.updated_counts.teams == 2
        assert result.updated_counts.players == 2
        assert result.updated_counts.player_team_tournaments == 2
        assert result.updated_counts.player_matches == 1
        assert result.conflicts.teams == []
        assert result.conflicts.players == []

        missing_titles = sorted([missing.title for missing in result.missing_positions])
        assert missing_titles == ["GOALIE", "GOALIE"]

        async with test_db.get_session_maker()() as session:
            updated_tournament = await session.get(type(tournament), tournament.id)
            assert updated_tournament is not None
            assert updated_tournament.sport_id == target_sport.id

            updated_team1 = await session.get(type(team1), team1.id)
            updated_team2 = await session.get(type(team2), team2.id)
            assert updated_team1 is not None
            assert updated_team2 is not None
            assert updated_team1.sport_id == target_sport.id
            assert updated_team2.sport_id == target_sport.id

            updated_player1 = await session.get(type(player1), player1.id)
            updated_player2 = await session.get(type(player2), player2.id)
            assert updated_player1 is not None
            assert updated_player2 is not None
            assert updated_player1.sport_id == target_sport.id
            assert updated_player2.sport_id == target_sport.id

            refreshed_ptt_forward = await session.get(PlayerTeamTournamentDB, ptt_forward.id)
            refreshed_ptt_goalie = await session.get(PlayerTeamTournamentDB, ptt_goalie.id)
            assert refreshed_ptt_forward is not None
            assert refreshed_ptt_goalie is not None
            assert refreshed_ptt_forward.position_id == target_forward.id
            assert refreshed_ptt_goalie.position_id is None

            refreshed_player_match = await session.get(PlayerMatchDB, player_match.id)
            assert refreshed_player_match is not None
            assert refreshed_player_match.match_position_id is None

    async def test_move_tournament_to_sport_blocks_team_conflicts(self, test_db):
        sport_service = SportServiceDB(test_db)
        source_sport = await sport_service.create(SportFactorySample.build())
        target_sport = await sport_service.create(SportFactoryAny.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )
        other_tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        shared_team = await team_service.create_or_update_team(
            TeamFactory.build(sport_id=source_sport.id, team_eesl_id=4001, title="Shared Team")
        )

        from src.core.models.team_tournament import TeamTournamentDB

        async with test_db.get_session_maker()() as session:
            session.add_all(
                [
                    TeamTournamentDB(tournament_id=tournament.id, team_id=shared_team.id),
                    TeamTournamentDB(tournament_id=other_tournament.id, team_id=shared_team.id),
                ]
            )
            await session.flush()

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await tournament_service.move_tournament_to_sport(
                tournament_id=tournament.id,
                target_sport_id=target_sport.id,
                move_conflicting_tournaments=False,
            )

        assert exc_info.value.status_code == 409
        detail = exc_info.value.detail
        assert isinstance(detail, dict)
        assert "conflicts" in detail
        conflicts = detail["conflicts"]
        assert len(conflicts["teams"]) == 1
        assert conflicts["teams"][0].entity_id == shared_team.id
        assert other_tournament.id in conflicts["teams"][0].tournament_ids

    async def test_move_tournament_to_sport_moves_conflicting_tournaments(self, test_db):
        sport_service = SportServiceDB(test_db)
        source_sport = await sport_service.create(SportFactorySample.build())
        target_sport = await sport_service.create(SportFactoryAny.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )
        other_tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        shared_team = await team_service.create_or_update_team(
            TeamFactory.build(sport_id=source_sport.id, team_eesl_id=4002, title="Shared Team")
        )

        from src.core.models.team_tournament import TeamTournamentDB

        async with test_db.get_session_maker()() as session:
            session.add_all(
                [
                    TeamTournamentDB(tournament_id=tournament.id, team_id=shared_team.id),
                    TeamTournamentDB(tournament_id=other_tournament.id, team_id=shared_team.id),
                ]
            )
            await session.flush()

        result = await tournament_service.move_tournament_to_sport(
            tournament_id=tournament.id,
            target_sport_id=target_sport.id,
            move_conflicting_tournaments=True,
        )

        assert result.moved is True
        assert sorted(result.moved_tournaments) == sorted([tournament.id, other_tournament.id])
        assert result.updated_counts.tournament == 2

        async with test_db.get_session_maker()() as session:
            from src.core.models import TeamDB, TournamentDB

            updated_main = await session.get(TournamentDB, tournament.id)
            updated_other = await session.get(TournamentDB, other_tournament.id)
            updated_team = await session.get(TeamDB, shared_team.id)
            assert updated_main is not None
            assert updated_main.sport_id == target_sport.id
            assert updated_other is not None
            assert updated_other.sport_id == target_sport.id
            assert updated_team is not None
            assert updated_team.sport_id == target_sport.id

    async def test_move_tournament_to_sport_blocks_player_conflicts(self, test_db):
        sport_service = SportServiceDB(test_db)
        source_sport = await sport_service.create(SportFactorySample.build())
        target_sport = await sport_service.create(SportFactoryAny.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )
        other_tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )

        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        person = await person_service.create(
            PersonSchemaCreateType(first_name="Casey", second_name="Shared")
        )
        player = await player_service.create(
            PlayerSchemaCreateType(
                sport_id=source_sport.id, person_id=person.id, player_eesl_id=9100
            )
        )

        from src.core.models.player_team_tournament import PlayerTeamTournamentDB

        async with test_db.get_session_maker()() as session:
            session.add_all(
                [
                    PlayerTeamTournamentDB(
                        player_id=player.id, tournament_id=tournament.id, team_id=None
                    ),
                    PlayerTeamTournamentDB(
                        player_id=player.id, tournament_id=other_tournament.id, team_id=None
                    ),
                ]
            )
            await session.flush()

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await tournament_service.move_tournament_to_sport(
                tournament_id=tournament.id,
                target_sport_id=target_sport.id,
                move_conflicting_tournaments=False,
            )

        assert exc_info.value.status_code == 409
        detail = exc_info.value.detail
        assert isinstance(detail, dict)
        assert "conflicts" in detail
        conflicts = detail["conflicts"]
        assert len(conflicts["players"]) == 1
        assert conflicts["players"][0].entity_id == player.id
        assert other_tournament.id in conflicts["players"][0].tournament_ids

    async def test_move_tournament_to_sport_moves_conflicting_player_tournaments(self, test_db):
        sport_service = SportServiceDB(test_db)
        source_sport = await sport_service.create(SportFactorySample.build())
        target_sport = await sport_service.create(SportFactoryAny.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )
        other_tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )

        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        person = await person_service.create(
            PersonSchemaCreateType(first_name="Casey", second_name="Shared")
        )
        player = await player_service.create(
            PlayerSchemaCreateType(
                sport_id=source_sport.id, person_id=person.id, player_eesl_id=9101
            )
        )

        from src.core.models.player_team_tournament import PlayerTeamTournamentDB

        async with test_db.get_session_maker()() as session:
            session.add_all(
                [
                    PlayerTeamTournamentDB(
                        player_id=player.id, tournament_id=tournament.id, team_id=None
                    ),
                    PlayerTeamTournamentDB(
                        player_id=player.id, tournament_id=other_tournament.id, team_id=None
                    ),
                ]
            )
            await session.flush()

        result = await tournament_service.move_tournament_to_sport(
            tournament_id=tournament.id,
            target_sport_id=target_sport.id,
            move_conflicting_tournaments=True,
        )

        assert result.moved is True
        assert sorted(result.moved_tournaments) == sorted([tournament.id, other_tournament.id])
        assert result.updated_counts.tournament == 2

        async with test_db.get_session_maker()() as session:
            from src.core.models import PlayerDB, TournamentDB

            updated_main = await session.get(TournamentDB, tournament.id)
            updated_other = await session.get(TournamentDB, other_tournament.id)
            updated_player = await session.get(PlayerDB, player.id)
            assert updated_main is not None
            assert updated_main.sport_id == target_sport.id
            assert updated_other is not None
            assert updated_other.sport_id == target_sport.id
            assert updated_player is not None
            assert updated_player.sport_id == target_sport.id

    async def test_move_tournament_to_sport_preview_with_conflicts(self, test_db):
        sport_service = SportServiceDB(test_db)
        source_sport = await sport_service.create(SportFactorySample.build())
        target_sport = await sport_service.create(SportFactoryAny.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )
        other_tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        shared_team = await team_service.create_or_update_team(
            TeamFactory.build(sport_id=source_sport.id, team_eesl_id=4003, title="Shared Team")
        )

        from src.core.models.team_tournament import TeamTournamentDB

        async with test_db.get_session_maker()() as session:
            session.add_all(
                [
                    TeamTournamentDB(tournament_id=tournament.id, team_id=shared_team.id),
                    TeamTournamentDB(tournament_id=other_tournament.id, team_id=shared_team.id),
                ]
            )
            await session.flush()

        result = await tournament_service.move_tournament_to_sport(
            tournament_id=tournament.id,
            target_sport_id=target_sport.id,
            move_conflicting_tournaments=True,
            preview=True,
        )

        assert result.moved is False
        assert result.preview is True
        assert sorted(result.moved_tournaments) == sorted([tournament.id, other_tournament.id])
        assert len(result.conflicts.teams) == 1
        assert result.conflicts.teams[0].entity_id == shared_team.id

        async with test_db.get_session_maker()() as session:
            from src.core.models import TournamentDB

            unchanged_main = await session.get(TournamentDB, tournament.id)
            unchanged_other = await session.get(TournamentDB, other_tournament.id)
            assert unchanged_main is not None
            assert unchanged_main.sport_id == source_sport.id
            assert unchanged_other is not None
            assert unchanged_other.sport_id == source_sport.id

    async def test_move_tournament_to_sport_preview_no_conflicts(self, test_db):
        sport_service = SportServiceDB(test_db)
        source_sport = await sport_service.create(SportFactorySample.build())
        target_sport = await sport_service.create(SportFactoryAny.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=source_sport.id, season_id=season.id)
        )

        result = await tournament_service.move_tournament_to_sport(
            tournament_id=tournament.id,
            target_sport_id=target_sport.id,
            preview=True,
        )

        assert result.moved is False
        assert result.preview is True
        assert result.moved_tournaments == [tournament.id]
        assert result.conflicts.teams == []
        assert result.conflicts.players == []

        async with test_db.get_session_maker()() as session:
            from src.core.models import TournamentDB

            unchanged = await session.get(TournamentDB, tournament.id)
            assert unchanged is not None
            assert unchanged.sport_id == source_sport.id
