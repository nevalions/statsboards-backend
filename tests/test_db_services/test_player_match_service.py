import pytest
from src.player_match.db_services import PlayerMatchServiceDB
from src.player_match.schemas import PlayerMatchSchemaCreate, PlayerMatchSchemaUpdate
from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
from src.player_team_tournament.schemas import PlayerTeamTournamentSchemaCreate
from src.player.db_services import PlayerServiceDB
from src.player.schemas import PlayerSchemaCreate
from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaCreate
from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.positions.db_services import PositionServiceDB
from src.positions.schemas import PositionSchemaCreate
from tests.factories import (
    MatchFactory,
    TeamFactory,
    TournamentFactory,
    SeasonFactorySample,
    SportFactorySample,
    PersonFactory,
    PlayerFactory,
    PositionFactory,
)
from src.logging_config import setup_logging

setup_logging()


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
        position = await position_service.create(
            PositionFactory.build(sport_id=sport.id)
        )

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
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
            )
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
        position = await position_service.create(
            PositionFactory.build(sport_id=sport.id)
        )

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
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_data = PlayerMatchSchemaCreate(
            match_id=match.id,
            player_team_tournament_id=player_tournament.id,
            team_id=team.id,
            player_match_eesl_id=100,
            match_number="1",
        )

        result = await player_match_service.create_or_update_player_match(
            player_match_data
        )

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
        position = await position_service.create(
            PositionFactory.build(sport_id=sport.id)
        )

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
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_data = PlayerMatchSchemaCreate(
            match_id=match.id,
            player_team_tournament_id=player_tournament.id,
            team_id=team.id,
            player_match_eesl_id=200,
        )

        created = await player_match_service.create_new_player_match(player_match_data)
        result = await player_match_service.get_player_match_by_match_id_and_eesl_id(
            match.id, 200
        )

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
        position = await position_service.create(
            PositionFactory.build(sport_id=sport.id)
        )

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
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
            )
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
        assert updated.is_start == True
