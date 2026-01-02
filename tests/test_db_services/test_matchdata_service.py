import pytest

from src.matchdata.db_services import MatchDataServiceDB
from src.matchdata.schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate
from src.matches.db_services import MatchServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    MatchFactory,
    SeasonFactorySample,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
class TestMatchDataServiceDB:
    async def test_create_matchdata(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = MatchDataSchemaCreate(
            match_id=match.id,
            field_length=92,
            game_status="in-progress",
            score_team_a=0,
            score_team_b=0,
            qtr="1st",
        )

        result = await matchdata_service.create(matchdata)

        assert result is not None
        assert result.id is not None
        assert result.match_id == match.id
        assert result.game_status == "in-progress"

    async def test_update_matchdata(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = MatchDataSchemaCreate(
            match_id=match.id, score_team_a=0, score_team_b=0
        )

        created = await matchdata_service.create(matchdata)
        update_data = MatchDataSchemaUpdate(score_team_a=7, score_team_b=3, qtr="2nd")

        updated = await matchdata_service.update(created.id, update_data)

        assert updated.score_team_a == 7
        assert updated.score_team_b == 3
        assert updated.qtr == "2nd"

    async def test_get_match_data_by_match_id(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        matchdata_service = MatchDataServiceDB(test_db)
        matchdata = MatchDataSchemaCreate(
            match_id=match.id, score_team_a=0, score_team_b=0
        )

        created = await matchdata_service.create(matchdata)
        result = await matchdata_service.get_match_data_by_match_id(match.id)

        assert result is not None
        assert result.id == created.id

    async def test_get_match_data_by_match_id_not_found(self, test_db):
        matchdata_service = MatchDataServiceDB(test_db)
        result = await matchdata_service.get_match_data_by_match_id(99999)

        assert result is None

    async def test_get_match_data_by_match_id_empty(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        matchdata_service = MatchDataServiceDB(test_db)
        result = await matchdata_service.get_match_data_by_match_id(match.id)

        assert result is None
