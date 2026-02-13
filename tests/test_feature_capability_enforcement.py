import pytest

from src.helpers.fetch_helpers import fetch_playclock, fetch_with_scoreboard_data
from src.matches.db_services import MatchServiceDB
from src.scoreboards.db_services import ScoreboardServiceDB
from src.scoreboards.schemas import ScoreboardSchemaCreate, ScoreboardSchemaUpdate
from src.seasons.db_services import SeasonServiceDB
from src.sport_scoreboard_preset.db_services import SportScoreboardPresetServiceDB
from src.sport_scoreboard_preset.schemas import SportScoreboardPresetSchemaCreate
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    MatchFactory,
    SeasonFactorySample,
    SportFactoryAny,
    TeamFactory,
    TournamentFactory,
)


async def _create_match_with_preset(
    test_db,
    *,
    has_playclock: bool,
    has_timeouts: bool,
    quick_score_deltas: list[int] | None = None,
    score_form_goal_label: str = "TD",
    score_form_goal_emoji: str = "🏈",
    scoreboard_goal_text: str = "TOUCHDOWN",
) -> int:
    preset_service = SportScoreboardPresetServiceDB(test_db)
    sport_service = SportServiceDB(test_db)
    season_service = SeasonServiceDB(test_db)
    tournament_service = TournamentServiceDB(test_db)
    team_service = TeamServiceDB(test_db)
    match_service = MatchServiceDB(test_db)

    preset = await preset_service.create(
        SportScoreboardPresetSchemaCreate(
            title="Capability Preset",
            has_playclock=has_playclock,
            has_timeouts=has_timeouts,
            is_playclock=True,
            quick_score_deltas=quick_score_deltas or [6, 3, 2, 1, -1],
            score_form_goal_label=score_form_goal_label,
            score_form_goal_emoji=score_form_goal_emoji,
            scoreboard_goal_text=scoreboard_goal_text,
        )
    )
    sport = await sport_service.create(SportFactoryAny.build(scoreboard_preset_id=preset.id))
    season = await season_service.create(SeasonFactorySample.build())
    tournament = await tournament_service.create(
        TournamentFactory.build(sport_id=sport.id, season_id=season.id)
    )
    team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
    team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))
    match = await match_service.create(
        MatchFactory.build(tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id)
    )
    return match.id


@pytest.mark.asyncio
class TestCapabilityEnforcement:
    async def test_fetch_playclock_not_supported_has_consistent_semantics(self, test_db):
        from src.playclocks.db_services import PlayClockServiceDB

        match_id = await _create_match_with_preset(
            test_db,
            has_playclock=False,
            has_timeouts=True,
        )

        playclock_payload = await fetch_playclock(match_id, database=test_db)
        assert playclock_payload is not None
        assert playclock_payload["match_id"] == match_id
        assert playclock_payload["playclock"] is None
        assert playclock_payload["is_supported"] is False

        playclock = await PlayClockServiceDB(test_db).get_playclock_by_match_id(match_id)
        assert playclock is None

    async def test_fetch_playclock_supported_still_auto_creates(self, test_db):
        from src.playclocks.db_services import PlayClockServiceDB

        match_id = await _create_match_with_preset(
            test_db,
            has_playclock=True,
            has_timeouts=True,
        )

        playclock_payload = await fetch_playclock(match_id, database=test_db)
        assert playclock_payload is not None
        assert playclock_payload["is_supported"] is True
        assert playclock_payload["playclock"] is not None

        playclock = await PlayClockServiceDB(test_db).get_playclock_by_match_id(match_id)
        assert playclock is not None

    async def test_scoreboard_update_cannot_enable_unsupported_features(self, test_db):
        match_id = await _create_match_with_preset(
            test_db,
            has_playclock=False,
            has_timeouts=False,
        )
        scoreboard_service = ScoreboardServiceDB(test_db)

        created = await scoreboard_service.create(
            ScoreboardSchemaCreate(
                match_id=match_id,
                is_playclock=True,
                is_timeout_team_a=True,
                is_timeout_team_b=True,
            )
        )
        assert created.is_playclock is False
        assert created.is_timeout_team_a is False
        assert created.is_timeout_team_b is False

        updated = await scoreboard_service.update(
            created.id,
            ScoreboardSchemaUpdate(
                is_playclock=True,
                is_timeout_team_a=True,
                is_timeout_team_b=True,
            ),
        )
        assert updated.is_playclock is False
        assert updated.is_timeout_team_a is False
        assert updated.is_timeout_team_b is False

    async def test_scoreboard_bootstrap_respects_timeout_capability(self, test_db):
        match_id = await _create_match_with_preset(
            test_db,
            has_playclock=True,
            has_timeouts=False,
        )

        full_payload = await fetch_with_scoreboard_data(match_id, database=test_db)
        assert full_payload is not None

        scoreboard = full_payload["data"]["scoreboard_data"]
        assert scoreboard["is_timeout_team_a"] is False
        assert scoreboard["is_timeout_team_b"] is False

    async def test_scoreboard_data_includes_has_timeouts_and_has_playclock_flags(self, test_db):
        match_id = await _create_match_with_preset(
            test_db,
            has_playclock=True,
            has_timeouts=True,
        )

        full_payload = await fetch_with_scoreboard_data(match_id, database=test_db)
        assert full_payload is not None

        scoreboard = full_payload["data"]["scoreboard_data"]
        assert "has_timeouts" in scoreboard
        assert "has_playclock" in scoreboard
        assert scoreboard["has_timeouts"] is True
        assert scoreboard["has_playclock"] is True

    async def test_scoreboard_data_flags_false_when_preset_disables(self, test_db):
        match_id = await _create_match_with_preset(
            test_db,
            has_playclock=False,
            has_timeouts=False,
        )

        full_payload = await fetch_with_scoreboard_data(match_id, database=test_db)
        assert full_payload is not None

        scoreboard = full_payload["data"]["scoreboard_data"]
        assert "has_timeouts" in scoreboard
        assert "has_playclock" in scoreboard
        assert scoreboard["has_timeouts"] is False
        assert scoreboard["has_playclock"] is False

    async def test_scoreboard_data_includes_custom_quick_score_deltas(self, test_db):
        match_id = await _create_match_with_preset(
            test_db,
            has_playclock=True,
            has_timeouts=True,
            quick_score_deltas=[1, -1],
        )

        full_payload = await fetch_with_scoreboard_data(match_id, database=test_db)
        assert full_payload is not None

        scoreboard = full_payload["data"]["scoreboard_data"]
        assert "quick_score_deltas" in scoreboard
        assert scoreboard["quick_score_deltas"] == [1, -1]

    async def test_scoreboard_data_falls_back_to_default_quick_score_deltas(self, test_db):
        match_id = await _create_match_with_preset(
            test_db,
            has_playclock=True,
            has_timeouts=True,
        )

        full_payload = await fetch_with_scoreboard_data(match_id, database=test_db)
        assert full_payload is not None

        scoreboard = full_payload["data"]["scoreboard_data"]
        assert "quick_score_deltas" in scoreboard
        assert scoreboard["quick_score_deltas"] == [6, 3, 2, 1, -1]

    async def test_scoreboard_data_includes_goal_metadata_defaults(self, test_db):
        match_id = await _create_match_with_preset(
            test_db,
            has_playclock=True,
            has_timeouts=True,
        )

        full_payload = await fetch_with_scoreboard_data(match_id, database=test_db)
        assert full_payload is not None

        scoreboard = full_payload["data"]["scoreboard_data"]
        assert scoreboard["score_form_goal_label"] == "TD"
        assert scoreboard["score_form_goal_emoji"] == "🏈"
        assert scoreboard["scoreboard_goal_text"] == "TOUCHDOWN"

    async def test_scoreboard_data_includes_custom_goal_metadata(self, test_db):
        match_id = await _create_match_with_preset(
            test_db,
            has_playclock=True,
            has_timeouts=True,
            score_form_goal_label="GOAL",
            score_form_goal_emoji="⚽",
            scoreboard_goal_text="GOAL",
        )

        full_payload = await fetch_with_scoreboard_data(match_id, database=test_db)
        assert full_payload is not None

        scoreboard = full_payload["data"]["scoreboard_data"]
        assert scoreboard["score_form_goal_label"] == "GOAL"
        assert scoreboard["score_form_goal_emoji"] == "⚽"
        assert scoreboard["scoreboard_goal_text"] == "GOAL"
