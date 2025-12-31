import pytest

from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.team_tournament.db_services import TeamTournamentServiceDB
from src.team_tournament.schemas import TeamTournamentSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    SeasonFactorySample,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)



@pytest.mark.asyncio
class TestTeamTournamentServiceDB:
    async def test_create_team_tournament(self, test_db):
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

        team_tournament_service = TeamTournamentServiceDB(test_db)
        team_tournament_data = TeamTournamentSchemaCreate(
            team_id=team.id, tournament_id=tournament.id
        )

        result = await team_tournament_service.create(team_tournament_data)

        assert result is not None
        assert result.id is not None
        assert result.team_id == team.id
        assert result.tournament_id == tournament.id

    async def test_create_duplicate_team_tournament(self, test_db):
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

        team_tournament_service = TeamTournamentServiceDB(test_db)
        team_tournament_data = TeamTournamentSchemaCreate(
            team_id=team.id, tournament_id=tournament.id
        )

        result1 = await team_tournament_service.create(team_tournament_data)
        result2 = await team_tournament_service.create(team_tournament_data)

        assert result1 is not None
        assert result2 is not None
        assert result1.id == result2.id

    async def test_get_team_tournament_relation(self, test_db):
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

        team_tournament_service = TeamTournamentServiceDB(test_db)
        team_tournament_data = TeamTournamentSchemaCreate(
            team_id=team.id, tournament_id=tournament.id
        )

        created = await team_tournament_service.create(team_tournament_data)
        result = await team_tournament_service.get_team_tournament_relation(
            team.id, tournament.id
        )

        assert result is not None
        assert result.id == created.id

    async def test_get_related_teams(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team1 = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team2 = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team3 = await team_service.create(TeamFactory.build(sport_id=sport.id))

        team_tournament_service = TeamTournamentServiceDB(test_db)
        await team_tournament_service.create(
            TeamTournamentSchemaCreate(team_id=team1.id, tournament_id=tournament.id)
        )
        await team_tournament_service.create(
            TeamTournamentSchemaCreate(team_id=team2.id, tournament_id=tournament.id)
        )
        await team_tournament_service.create(
            TeamTournamentSchemaCreate(team_id=team3.id, tournament_id=tournament.id)
        )

        result = await team_tournament_service.get_related_teams(tournament.id)

        assert result is not None
        assert len(result) == 3

    async def test_delete_relation_by_team_and_tournament_id(self, test_db):
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

        team_tournament_service = TeamTournamentServiceDB(test_db)
        await team_tournament_service.create(
            TeamTournamentSchemaCreate(team_id=team.id, tournament_id=tournament.id)
        )

        await team_tournament_service.delete_relation_by_team_and_tournament_id(
            team.id, tournament.id
        )

        result = await team_tournament_service.get_team_tournament_relation(
            team.id, tournament.id
        )

        assert result is None

    async def test_delete_relation_not_found(self, test_db):
        from fastapi import HTTPException

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

        team_tournament_service = TeamTournamentServiceDB(test_db)

        with pytest.raises(HTTPException) as exc_info:
            await team_tournament_service.delete_relation_by_team_and_tournament_id(
                team.id, tournament.id
            )

        assert exc_info.value.status_code == 404
