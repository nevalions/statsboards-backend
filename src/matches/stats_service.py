from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.models import (
    BaseServiceDB,
    FootballEventDB,
    MatchDB,
    PlayerMatchDB,
    handle_service_exceptions,
)
from src.core.models.base import Database
from src.logging_config import get_logger

if TYPE_CHECKING:
    pass

ITEM = "MATCH_STATS"


class MatchStatsServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(database, MatchDB)
        self.logger = get_logger("backend_logger_MatchStatsServiceDB", self)
        self.logger.debug("Initialized MatchStatsServiceDB")
        self._cache: dict[int, dict] = {}

    @handle_service_exceptions(
        item_name=ITEM,
        operation="calculating team stats",
    )
    async def calculate_team_stats(
        self,
        match_id: int,
        team_id: int,
    ) -> dict:
        self.logger.debug(f"Calculating team stats for match {match_id}, team {team_id}")
        async with self.db.async_session() as session:
            stmt = select(FootballEventDB).where(FootballEventDB.match_id == match_id)
            results = await session.execute(stmt)
            events = results.scalars().all()

            player_match_ids = set()
            for event in events:
                if event.fumble_recovered_player:
                    player_match_ids.add(event.fumble_recovered_player)

            player_matches = {}
            if player_match_ids:
                pm_stmt = select(PlayerMatchDB).where(PlayerMatchDB.id.in_(player_match_ids))
                pm_results = await session.execute(pm_stmt)
                for pm in pm_results.scalars().all():
                    player_matches[pm.id] = pm.team_id

            run_yards = 0
            pass_yards = 0
            lost_yards = 0
            run_attempts = 0
            pass_attempts = 0
            flag_yards_offence = 0
            flag_yards_defence = 0
            turnovers = 0

            third_down_attempts = 0
            third_down_conversions = 0
            fourth_down_attempts = 0
            fourth_down_conversions = 0
            first_down_gained = 0

            prev_offense_team = None
            prev_down = None

            for event in events:
                if event.offense_team != team_id:
                    flag_yards_defence += self._calculate_flag_yards_on_defence(event)

                if event.offense_team == team_id:
                    run_y, pass_y, lost = self._calculate_run_pass_distance(event)
                    run_yards += run_y
                    pass_yards += pass_y
                    lost_yards += lost

                    if event.play_type == "run" and event.play_result not in ["flag"]:
                        run_attempts += 1
                    if event.play_type == "pass" and event.play_result not in ["flag"]:
                        pass_attempts += 1

                    flag_yards_offence += self._calculate_flag_yards_on_offence(event)

                    turnovers += self._calculate_turnovers(event, team_id, player_matches)

                    down_stats = self._calculate_down_stats(
                        event,
                        prev_offense_team,
                        prev_down,
                        team_id,
                    )
                    third_down_attempts += down_stats["third_down_attempts"]
                    third_down_conversions += down_stats["third_down_conversions"]
                    fourth_down_attempts += down_stats["fourth_down_attempts"]
                    fourth_down_conversions += down_stats["fourth_down_conversions"]
                    first_down_gained += down_stats["first_down_gained"]

                    prev_offense_team = event.offense_team
                    prev_down = event.event_down

            total_yards = run_yards + pass_yards
            total_attempts = run_attempts + pass_attempts
            avg_yards_per_att = (
                round(total_yards / total_attempts, 2) if total_attempts > 0 else 0.0
            )

            total_flag_yards = flag_yards_offence + flag_yards_defence

            return {
                "id": team_id,
                "offence_yards": total_yards,
                "pass_att": pass_attempts,
                "run_att": run_attempts,
                "avg_yards_per_att": avg_yards_per_att,
                "pass_yards": pass_yards,
                "run_yards": run_yards,
                "lost_yards": lost_yards,
                "flag_yards": -total_flag_yards,
                "third_down_attempts": third_down_attempts,
                "third_down_conversions": third_down_conversions,
                "fourth_down_attempts": fourth_down_attempts,
                "fourth_down_conversions": fourth_down_conversions,
                "first_down_gained": first_down_gained,
                "turnovers": turnovers,
            }

    def _calculate_run_pass_distance(self, event: FootballEventDB) -> tuple[int, int, int]:
        run_yards = 0
        pass_yards = 0
        lost_yards = 0

        distance_moved = (
            (event.ball_moved_to or 0) - (event.ball_on or 0)
            if event.ball_moved_to and event.ball_on
            else event.distance_on_offence or 0
        )

        if event.play_type in ["run", "pass"]:
            if event.play_result == "sack" or (event.play_result == "run" and event.is_fumble):
                if distance_moved and distance_moved < 0:
                    lost_yards += abs(distance_moved)
            elif (
                event.play_type == "run" or event.play_type == "pass"
            ) and event.play_result == "run":
                run_yards += distance_moved if not event.is_fumble else distance_moved
            elif event.play_type == "pass" and event.play_result == "completed":
                pass_yards += distance_moved if not event.is_fumble else distance_moved

        return run_yards, pass_yards, lost_yards

    def _calculate_flag_yards_on_offence(self, event: FootballEventDB) -> int:
        if event.play_result == "flag":
            distance_moved = (
                (event.ball_moved_to or 0) - (event.ball_on or 0)
                if event.ball_moved_to and event.ball_on
                else event.distance_on_offence or 0
            )
            if distance_moved and distance_moved < 0:
                return distance_moved
        return 0

    def _calculate_flag_yards_on_defence(self, event: FootballEventDB) -> int:
        if event.play_result == "flag":
            distance_moved = (
                (event.ball_moved_to or 0) - (event.ball_on or 0)
                if event.ball_moved_to and event.ball_on
                else event.distance_on_offence or 0
            )
            if distance_moved and distance_moved > 0:
                return -distance_moved
        return 0

    def _calculate_turnovers(
        self, event: FootballEventDB, team_id: int, player_matches: dict[int, int]
    ) -> int:
        if event.offense_team != team_id:
            return 0

        if event.play_result == "intercepted":
            return 1

        if event.is_fumble:
            if event.fumble_recovered_player:
                recovering_team_id = player_matches.get(event.fumble_recovered_player)
                if recovering_team_id and recovering_team_id != team_id:
                    return 1

        return 0

    def _calculate_down_stats(
        self,
        event: FootballEventDB,
        prev_offense_team: int | None,
        prev_down: int | None,
        team_id: int,
    ) -> dict:
        third_down_attempts = 0
        third_down_conversions = 0
        fourth_down_attempts = 0
        fourth_down_conversions = 0
        first_down_gained = 0

        if (
            prev_offense_team is not None
            and prev_offense_team == team_id
            and event.offense_team != team_id
            and prev_down == 4
        ):
            fourth_down_attempts += 1

        if event.offense_team == team_id:
            if prev_offense_team is not None and prev_offense_team == team_id:
                if prev_down == 3:
                    third_down_attempts += 1
                    if event.event_down == 1 or event.score_result == "td":
                        third_down_conversions += 1
                elif prev_down == 4:
                    fourth_down_attempts += 1
                    if event.event_down == 1 or event.score_result == "td":
                        fourth_down_conversions += 1

            if event.event_down == 1 and prev_offense_team is not None:
                if prev_offense_team != team_id or event.event_down != 1:
                    first_down_gained += 1

        return {
            "third_down_attempts": third_down_attempts,
            "third_down_conversions": third_down_conversions,
            "fourth_down_attempts": fourth_down_attempts,
            "fourth_down_conversions": fourth_down_conversions,
            "first_down_gained": first_down_gained,
        }

    @handle_service_exceptions(
        item_name=ITEM,
        operation="calculating offense stats",
    )
    async def calculate_offense_stats(
        self,
        match_id: int,
        team_id: int,
    ) -> dict[int, dict]:
        self.logger.debug(f"Calculating offense stats for match {match_id}, team {team_id}")
        async with self.db.async_session() as session:
            stmt = (
                select(FootballEventDB)
                .where(FootballEventDB.match_id == match_id)
                .where(FootballEventDB.offense_team == team_id)
                .options(
                    selectinload(FootballEventDB.run_player_rel),
                    selectinload(FootballEventDB.pass_received_player_rel),
                )
            )
            results = await session.execute(stmt)
            events = results.scalars().all()

            offense_stats: dict[int, dict] = {}

            for event in events:
                player_id = None
                if event.run_player:
                    player_id = event.run_player
                elif event.pass_received_player:
                    player_id = event.pass_received_player

                if not player_id:
                    continue

                if player_id not in offense_stats:
                    offense_stats[player_id] = {
                        "id": player_id,
                        "pass_attempts": 0,
                        "pass_received": 0,
                        "pass_yards": 0,
                        "pass_td": 0,
                        "run_attempts": 0,
                        "run_yards": 0,
                        "run_avr": 0.0,
                        "run_td": 0,
                        "fumble": 0,
                    }

                if event.play_type == "pass":
                    self._calculate_pass_stats(event, player_id, offense_stats)
                elif event.play_type == "run":
                    self._calculate_run_stats(event, player_id, offense_stats)

                offense_stats[player_id]["run_avr"] = (
                    round(
                        offense_stats[player_id]["run_yards"]
                        / offense_stats[player_id]["run_attempts"],
                        2,
                    )
                    if offense_stats[player_id]["run_attempts"] > 0
                    else 0.0
                )

            return offense_stats

    def _calculate_pass_stats(
        self,
        event: FootballEventDB,
        player_id: int,
        stats: dict[int, dict],
    ) -> None:
        if event.play_result != "flag":
            if event.pass_received_player == player_id:
                stats[player_id]["pass_attempts"] += 1
                stats[player_id]["pass_received"] += 1
                if event.play_result == "completed":
                    distance_moved = (
                        (event.ball_moved_to or 0) - (event.ball_on or 0)
                        if event.ball_moved_to and event.ball_on
                        else event.distance_on_offence or 0
                    )
                    if not event.is_fumble:
                        stats[player_id]["pass_yards"] += distance_moved
                        if event.score_result == "td":
                            stats[player_id]["pass_td"] += 1
                    else:
                        stats[player_id]["pass_yards"] += event.distance_on_offence or 0
                        stats[player_id]["fumble"] += 1
                elif event.play_result in ["incomplete", "dropped", "deflected"]:
                    stats[player_id]["pass_attempts"] += 1
            elif event.play_result in ["incomplete", "dropped", "deflected"]:
                stats[player_id]["pass_attempts"] += 1

    def _calculate_run_stats(
        self,
        event: FootballEventDB,
        player_id: int,
        stats: dict[int, dict],
    ) -> None:
        if event.play_result != "flag":
            if event.run_player == player_id:
                stats[player_id]["run_attempts"] += 1
                distance_moved = (
                    (event.ball_moved_to or 0) - (event.ball_on or 0)
                    if event.ball_moved_to and event.ball_on
                    else event.distance_on_offence or 0
                )
                if not event.is_fumble:
                    stats[player_id]["run_yards"] += distance_moved
                    if event.score_result == "td":
                        stats[player_id]["run_td"] += 1
                else:
                    stats[player_id]["run_yards"] += event.distance_on_offence or 0
                    stats[player_id]["fumble"] += 1

    @handle_service_exceptions(
        item_name=ITEM,
        operation="calculating QB stats",
    )
    async def calculate_qb_stats(
        self,
        match_id: int,
        team_id: int,
    ) -> dict[int, dict]:
        self.logger.debug(f"Calculating QB stats for match {match_id}, team {team_id}")
        async with self.db.async_session() as session:
            stmt = (
                select(FootballEventDB)
                .where(FootballEventDB.match_id == match_id)
                .where(FootballEventDB.offense_team == team_id)
                .where(FootballEventDB.event_qb.isnot(None))
                .options(selectinload(FootballEventDB.event_qb_rel))
            )
            results = await session.execute(stmt)
            events = results.scalars().all()

            qb_stats: dict[int, dict] = {}

            for event in events:
                qb_id = event.event_qb
                if not qb_id:
                    continue

                if qb_id not in qb_stats:
                    qb_stats[qb_id] = {
                        "id": qb_id,
                        "passes": 0,
                        "passes_completed": 0,
                        "pass_yards": 0,
                        "pass_td": 0,
                        "pass_avr": 0.0,
                        "run_attempts": 0,
                        "run_yards": 0,
                        "run_td": 0,
                        "run_avr": 0.0,
                        "fumble": 0,
                        "interception": 0,
                        "qb_rating": 0.0,
                    }

                if event.play_type == "pass" and event.play_result != "flag":
                    qb_stats[qb_id]["passes"] += 1
                    if event.play_result == "completed":
                        qb_stats[qb_id]["passes_completed"] += 1
                        distance_moved = (
                            (event.ball_moved_to or 0) - (event.ball_on or 0)
                            if event.ball_moved_to and event.ball_on
                            else event.distance_on_offence or 0
                        )
                        if not event.is_fumble:
                            qb_stats[qb_id]["pass_yards"] += distance_moved
                            if event.score_result == "td":
                                qb_stats[qb_id]["pass_td"] += 1
                        else:
                            qb_stats[qb_id]["pass_yards"] += event.distance_on_offence or 0
                            qb_stats[qb_id]["fumble"] += 1
                    elif event.play_result == "intercepted":
                        qb_stats[qb_id]["interception"] += 1

                if event.play_type == "run" and event.play_result == "run":
                    qb_stats[qb_id]["run_attempts"] += 1
                    if not event.is_fumble:
                        distance_moved = (
                            (event.ball_moved_to or 0) - (event.ball_on or 0)
                            if event.ball_moved_to and event.ball_on
                            else event.distance_on_offence or 0
                        )
                        qb_stats[qb_id]["run_yards"] += distance_moved
                        if event.score_result == "td":
                            qb_stats[qb_id]["run_td"] += 1
                    else:
                        qb_stats[qb_id]["run_yards"] += event.distance_on_offence or 0
                        qb_stats[qb_id]["fumble"] += 1

                qb_stats[qb_id]["pass_avr"] = (
                    round(
                        (qb_stats[qb_id]["passes_completed"] / qb_stats[qb_id]["passes"]) * 100,
                        2,
                    )
                    if qb_stats[qb_id]["passes"] > 0
                    else 0.0
                )

                qb_stats[qb_id]["run_avr"] = (
                    round(
                        qb_stats[qb_id]["run_yards"] / qb_stats[qb_id]["run_attempts"],
                        2,
                    )
                    if qb_stats[qb_id]["run_attempts"] > 0
                    else 0.0
                )

                qb_stats[qb_id]["qb_rating"] = self._calculate_qb_rating(qb_stats[qb_id])

            return qb_stats

    def _calculate_qb_rating(self, stats: dict) -> float:
        if stats["passes"] == 0:
            return 0.0
        qb_rating = (
            8.4 * stats["pass_yards"]
            + 330 * stats["pass_td"]
            + 100 * stats["passes_completed"]
            - 200 * stats["interception"]
        ) / stats["passes"]
        return round(qb_rating, 2)

    @handle_service_exceptions(
        item_name=ITEM,
        operation="calculating defense stats",
    )
    async def calculate_defense_stats(
        self,
        match_id: int,
        team_id: int,
    ) -> dict[int, dict]:
        self.logger.debug(f"Calculating defense stats for match {match_id}, team {team_id}")
        async with self.db.async_session() as session:
            stmt = select(FootballEventDB).where(FootballEventDB.match_id == match_id)
            results = await session.execute(stmt)
            events = results.scalars().all()

            defense_stats: dict[int, dict] = {}

            for event in events:
                if event.offense_team == team_id:
                    continue

                players_to_check = []
                if event.tackle_player:
                    players_to_check.append((event.tackle_player, "tackles"))
                if event.assist_tackle_player:
                    players_to_check.append((event.assist_tackle_player, "assist_tackles"))
                if event.sack_player:
                    players_to_check.append((event.sack_player, "sacks"))
                if event.pass_intercepted_player:
                    players_to_check.append((event.pass_intercepted_player, "interceptions"))
                if event.fumble_recovered_player:
                    players_to_check.append((event.fumble_recovered_player, "fumble_recoveries"))
                if event.flagged_player and event.play_result == "flag":
                    players_to_check.append((event.flagged_player, "flags"))

                for player_id, stat_name in players_to_check:
                    if player_id not in defense_stats:
                        defense_stats[player_id] = {
                            "id": player_id,
                            "tackles": 0,
                            "assist_tackles": 0,
                            "sacks": 0,
                            "interceptions": 0,
                            "fumble_recoveries": 0,
                            "flags": 0,
                        }
                    defense_stats[player_id][stat_name] += 1

            return defense_stats

    @handle_service_exceptions(
        item_name=ITEM,
        operation="getting match with cached stats",
    )
    async def get_match_with_cached_stats(self, match_id: int) -> dict:
        self.logger.debug(f"Getting match {match_id} with cached stats")
        if match_id in self._cache:
            self.logger.debug(f"Returning cached stats for match {match_id}")
            return self._cache[match_id]

        async with self.db.async_session() as session:
            stmt = (
                select(MatchDB)
                .where(MatchDB.id == match_id)
                .options(selectinload(MatchDB.match_events))
            )
            result = await session.execute(stmt)
            match = result.scalar_one_or_none()

            if not match:
                return {}

            team_a_id = match.team_a_id
            team_b_id = match.team_b_id

            team_a_stats = await self.calculate_team_stats(match_id, team_a_id)
            team_b_stats = await self.calculate_team_stats(match_id, team_b_id)

            team_a_offense = await self.calculate_offense_stats(match_id, team_a_id)
            team_b_offense = await self.calculate_offense_stats(match_id, team_b_id)

            team_a_qb = await self.calculate_qb_stats(match_id, team_a_id)
            team_b_qb = await self.calculate_qb_stats(match_id, team_b_id)

            team_a_defense = await self.calculate_defense_stats(match_id, team_a_id)
            team_b_defense = await self.calculate_defense_stats(match_id, team_b_id)

            stats = {
                "match_id": match_id,
                "team_a": {
                    "id": team_a_id,
                    "team_stats": team_a_stats,
                    "offense_stats": team_a_offense,
                    "qb_stats": team_a_qb,
                    "defense_stats": team_a_defense,
                },
                "team_b": {
                    "id": team_b_id,
                    "team_stats": team_b_stats,
                    "offense_stats": team_b_offense,
                    "qb_stats": team_b_qb,
                    "defense_stats": team_b_defense,
                },
            }

            self._cache[match_id] = stats
            return stats

    def invalidate_cache(self, match_id: int) -> None:
        self.logger.debug(f"Invalidating cache for match {match_id}")
        if match_id in self._cache:
            del self._cache[match_id]
