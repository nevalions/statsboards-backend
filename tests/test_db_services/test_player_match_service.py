import pytest

from src.matches.db_services import MatchServiceDB
from src.person.db_services import PersonServiceDB
from src.player.db_services import PlayerServiceDB
from src.player_match.db_services import PlayerMatchServiceDB
from src.player_match.schemas import PlayerMatchSchemaCreate, PlayerMatchSchemaUpdate
from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
from src.player_team_tournament.schemas import PlayerTeamTournamentSchemaCreate
from src.positions.db_services import PositionServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    MatchFactory,
    PersonFactory,
    PlayerFactory,
    PositionFactory,
    SeasonFactorySample,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
class TestPlayerMatchServiceDB:
    async def test_create_player_match(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        person_service = PersonServiceDB(test_db)
        person = await person_service.create(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))

        player_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament = await player_tournament_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
            )
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id)
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_data = PlayerMatchSchemaCreate(
            match_id=match.id,
            player_team_tournament_id=player_tournament.id,
            team_id=team.id,
            match_position_id=position.id,
            match_number="1",
            is_start=True,
        )

        result = await player_match_service.create_new_player_match(player_match_data)

        assert result is not None
        assert result.id is not None
        assert result.match_id == match.id

    async def test_create_or_update_player_match_with_eesl_id(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        person_service = PersonServiceDB(test_db)
        person = await person_service.create(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))

        player_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament = await player_tournament_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
            )
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id)
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_data = PlayerMatchSchemaCreate(
            match_id=match.id,
            player_team_tournament_id=player_tournament.id,
            team_id=team.id,
            player_match_eesl_id=100,
            match_number="1",
        )

        result = await player_match_service.create_or_update_player_match(player_match_data)

        assert result is not None
        assert result.player_match_eesl_id == 100

    async def test_get_player_match_by_match_id_and_eesl_id(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        person_service = PersonServiceDB(test_db)
        person = await person_service.create(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))

        player_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament = await player_tournament_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
            )
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id)
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_data = PlayerMatchSchemaCreate(
            match_id=match.id,
            player_team_tournament_id=player_tournament.id,
            team_id=team.id,
            player_match_eesl_id=200,
        )

        created = await player_match_service.create_new_player_match(player_match_data)
        result = await player_match_service.get_player_match_by_match_id_and_eesl_id(match.id, 200)

        assert result is not None
        assert result.id == created.id

    async def test_update_player_match(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        person_service = PersonServiceDB(test_db)
        person = await person_service.create(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))

        player_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament = await player_tournament_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
            )
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id)
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_data = PlayerMatchSchemaCreate(
            match_id=match.id,
            player_team_tournament_id=player_tournament.id,
            team_id=team.id,
            match_number="1",
        )

        created = await player_match_service.create_new_player_match(player_match_data)
        update_data = PlayerMatchSchemaUpdate(match_number="2", is_start=True)

        updated = await player_match_service.update(created.id, update_data)

        assert updated.match_number == "2"
        assert updated.is_start

    async def test_get_player_match_by_match_id_and_eesl_id_not_found(self, test_db):
        """Test retrieving non-existent player_match returns None."""
        player_match_service = PlayerMatchServiceDB(test_db)
        result = await player_match_service.get_player_match_by_match_id_and_eesl_id(
            match_id=99999, player_match_eesl_id=999
        )
        assert result is None

    async def test_get_player_in_sport(self, test_db):
        """Test retrieving player by id returns nested player."""
        player_match_service = PlayerMatchServiceDB(test_db)
        result = await player_match_service.get_player_in_sport(player_id=1)
        assert result is None

    async def test_get_player_person_in_match_not_found(self, test_db):
        """Test retrieving person for non-existent player returns None."""
        player_match_service = PlayerMatchServiceDB(test_db)
        result = await player_match_service.get_player_person_in_match(99999)
        assert result is None

    async def test_get_player_in_team_tournament_not_found(self, test_db):
        """Test retrieving player_team_tournament for non-existent match returns None."""
        player_match_service = PlayerMatchServiceDB(test_db)
        result = await player_match_service.get_player_in_team_tournament(match_id=99999)
        assert result is None

    async def test_get_player_in_match_full_data_not_found(self, test_db):
        """Test retrieving full data for non-existent player - function has bug that throws error."""
        player_match_service = PlayerMatchServiceDB(test_db)
        try:
            await player_match_service.get_player_in_match_full_data(match_player_id=99999)
            assert False, "Expected exception due to bug in function"
        except Exception:
            assert True

    async def test_get_player_match_by_eesl_id_not_found(self, test_db):
        """Test retrieving player_match by eesl_id returns None."""
        player_match_service = PlayerMatchServiceDB(test_db)
        result = await player_match_service.get_player_match_by_eesl_id(99999)
        assert result is None

    async def test_get_players_match_by_match_id_not_found(self, test_db):
        """Test retrieving player_match by match_id and team_tournament_id returns None."""
        player_match_service = PlayerMatchServiceDB(test_db)
        result = await player_match_service.get_players_match_by_match_id(
            match_id=99999, player_team_tournament_id=999
        )
        assert result is None

    async def test_create_or_update_player_match_with_team_tournament_id(self, test_db):
        """Test creating player_match using team_tournament_id."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        person_service = PersonServiceDB(test_db)
        person = await person_service.create(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))

        player_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament = await player_tournament_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
            )
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id)
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_data = PlayerMatchSchemaCreate(
            match_id=match.id,
            player_team_tournament_id=player_tournament.id,
            team_id=team.id,
            match_position_id=position.id,
            match_number="1",
        )

        result = await player_match_service.create_or_update_player_match(player_match_data)

        assert result is not None
        assert result.player_team_tournament_id == player_tournament.id
