import pytest
from src.scoreboards.db_services import ScoreboardServiceDB
from src.scoreboards.schemas import ScoreboardSchemaCreate, ScoreboardSchemaUpdate
from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from src.seasons.db_services import SeasonServiceDB
from tests.factories import MatchFactory, TeamFactory, TournamentFactory, SeasonFactorySample, SportFactorySample
from src.logging_config import setup_logging

setup_logging()


@pytest.mark.asyncio
class TestScoreboardServiceDB:
    async def test_create_scoreboard(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        match_service = MatchServiceDB(test_db)
        match = await match_service.create(MatchFactory.build(tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id))
        
        scoreboard_service = ScoreboardServiceDB(test_db)
        scoreboard_data = ScoreboardSchemaCreate(
            match_id=match.id,
            is_qtr=True,
            is_time=True,
            is_downdistance=True
        )
        
        result = await scoreboard_service.create(scoreboard_data)
        
        assert result is not None
        assert result.id is not None
        assert result.match_id == match.id

    async def test_create_scoreboard_duplicate(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        match_service = MatchServiceDB(test_db)
        match = await match_service.create(MatchFactory.build(tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id))
        
        scoreboard_service = ScoreboardServiceDB(test_db)
        scoreboard_data = ScoreboardSchemaCreate(match_id=match.id, is_qtr=True)
        
        result1 = await scoreboard_service.create(scoreboard_data)
        result2 = await scoreboard_service.create(scoreboard_data)
        
        assert result1 is not None
        assert result2 is not None

    async def test_update_scoreboard(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        match_service = MatchServiceDB(test_db)
        match = await match_service.create(MatchFactory.build(tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id))
        
        scoreboard_service = ScoreboardServiceDB(test_db)
        scoreboard_data = ScoreboardSchemaCreate(
            match_id=match.id,
            is_qtr=True,
            is_time=False
        )
        
        created = await scoreboard_service.create(scoreboard_data)
        update_data = ScoreboardSchemaUpdate(is_time=True, is_playclock=True)
        
        updated = await scoreboard_service.update(created.id, update_data)
        
        assert updated.is_time == True
        assert updated.is_playclock == True

    async def test_get_scoreboard_by_match_id(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        match_service = MatchServiceDB(test_db)
        match = await match_service.create(MatchFactory.build(tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id))
        
        scoreboard_service = ScoreboardServiceDB(test_db)
        scoreboard_data = ScoreboardSchemaCreate(match_id=match.id, is_qtr=True)
        
        created = await scoreboard_service.create(scoreboard_data)
        result = await scoreboard_service.get_scoreboard_by_match_id(match.id)
        
        assert result is not None
        assert result.id == created.id

    async def test_create_or_update_scoreboard_create(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        match_service = MatchServiceDB(test_db)
        match = await match_service.create(MatchFactory.build(tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id))
        
        scoreboard_service = ScoreboardServiceDB(test_db)
        scoreboard_data = ScoreboardSchemaCreate(match_id=match.id, is_qtr=True)
        
        result = await scoreboard_service.create_or_update_scoreboard(scoreboard_data)
        
        assert result is not None
        assert result.match_id == match.id

    async def test_create_or_update_scoreboard_update(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        match_service = MatchServiceDB(test_db)
        match = await match_service.create(MatchFactory.build(tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id))
        
        scoreboard_service = ScoreboardServiceDB(test_db)
        create_data = ScoreboardSchemaCreate(match_id=match.id, is_qtr=True)
        created = await scoreboard_service.create_or_update_scoreboard(create_data)
        
        update_data = ScoreboardSchemaUpdate(match_id=match.id, is_time=True)
        updated = await scoreboard_service.create_or_update_scoreboard(update_data)
        
        assert updated.id == created.id
        assert updated.is_time == True
