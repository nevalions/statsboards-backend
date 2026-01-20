from typing import TYPE_CHECKING

from src.core.models.base import Database
from src.logging_config import get_logger

if TYPE_CHECKING:
    pass

ITEM = "MATCH_DATA_CACHE"


class MatchDataCacheService:
    def __init__(self, database: Database) -> None:
        self.db = database
        self.logger = get_logger("backend_logger_MatchDataCacheService", self)
        self.logger.debug("Initialized MatchDataCacheService")
        self._cache: dict[str, dict] = {}

    async def get_or_fetch_match_data(self, match_id: int) -> dict | None:
        cache_key = f"match-update:{match_id}"
        if cache_key in self._cache:
            self.logger.debug(f"Returning cached match data for match {match_id}")
            return self._cache[cache_key]

        self.logger.debug(f"Fetching match data for match {match_id}")
        from src.helpers.fetch_helpers import fetch_with_scoreboard_data

        result = await fetch_with_scoreboard_data(match_id, database=self.db)
        if result and result.get("status_code") == 200:
            self._cache[cache_key] = result
            self.logger.debug(f"Cached match data for match {match_id}")
            return result
        return None

    async def get_or_fetch_gameclock(self, match_id: int) -> dict | None:
        cache_key = f"gameclock-update:{match_id}"
        if cache_key in self._cache:
            self.logger.debug(f"Returning cached gameclock for match {match_id}")
            return self._cache[cache_key]

        self.logger.debug(f"Fetching gameclock for match {match_id}")
        from src.helpers.fetch_helpers import fetch_gameclock

        result = await fetch_gameclock(match_id, database=self.db)
        if result and result.get("status_code") == 200:
            self._cache[cache_key] = result
            self.logger.debug(f"Cached gameclock for match {match_id}")
            return result
        return None

    async def get_or_fetch_playclock(self, match_id: int) -> dict | None:
        cache_key = f"playclock-update:{match_id}"
        if cache_key in self._cache:
            self.logger.debug(f"Returning cached playclock for match {match_id}")
            return self._cache[cache_key]

        self.logger.debug(f"Fetching playclock for match {match_id}")
        from src.helpers.fetch_helpers import fetch_playclock

        result = await fetch_playclock(match_id, database=self.db)
        if result and result.get("status_code") == 200:
            self._cache[cache_key] = result
            self.logger.debug(f"Cached playclock for match {match_id}")
            return result
        return None

    def invalidate_match_data(self, match_id: int) -> None:
        cache_key = f"match-update:{match_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
            self.logger.debug(f"Invalidated match data cache for match {match_id}")

    def invalidate_gameclock(self, match_id: int) -> None:
        cache_key = f"gameclock-update:{match_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
            self.logger.debug(f"Invalidated gameclock cache for match {match_id}")

    def invalidate_playclock(self, match_id: int) -> None:
        cache_key = f"playclock-update:{match_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
            self.logger.debug(f"Invalidated playclock cache for match {match_id}")

    async def get_or_fetch_event_data(self, match_id: int) -> dict | None:
        cache_key = f"event-update:{match_id}"
        if cache_key in self._cache:
            self.logger.debug(f"Returning cached event data for match {match_id}")
            return self._cache[cache_key]

        self.logger.debug(f"Fetching event data for match {match_id}")
        from src.helpers.fetch_helpers import fetch_event

        result = await fetch_event(match_id, database=self.db)
        if result and result.get("status_code") == 200:
            self._cache[cache_key] = result
            self.logger.debug(f"Cached event data for match {match_id}")
            return result
        return None

    def invalidate_event_data(self, match_id: int) -> None:
        cache_key = f"event-update:{match_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
            self.logger.debug(f"Invalidated event data cache for match {match_id}")
