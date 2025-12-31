from fastapi import APIRouter

from src.core import MinimalBaseRouter
from src.logging_config import get_logger
from src.matches.parser import match_parser
from .db_services import MatchServiceDB
from .schemas import (
    MatchSchema,
    MatchSchemaCreate,
    MatchSchemaUpdate,
)


class MatchParserRouter(
    MinimalBaseRouter[
        MatchSchema,
        MatchSchemaCreate,
        MatchSchemaUpdate,
    ]
):
    def __init__(self, service: MatchServiceDB):
        super().__init__(
            "/api/matches",
            ["matches-parser"],
            service,
        )
        self.logger = get_logger("backend_logger_MatchParserRouter", self)
        self.logger.debug("Initialized MatchParserRouter")

    def route(self):
        router = APIRouter(prefix=self.prefix, tags=self.tags)

        @router.get(
            "/pars/tournament/{eesl_tournament_id}",
        )
        async def get_parse_tournament_matches(eesl_tournament_id: int):
            return await match_parser.get_parse_tournament_matches(eesl_tournament_id)

        @router.get("/pars_and_create/tournament/{eesl_tournament_id}")
        async def create_parsed_matches_endpoint(
            eesl_tournament_id: int,
        ):
            self.logger.debug(
                f"Get and Save parsed matches from tournament eesl_id:{eesl_tournament_id} endpoint"
            )
            return await match_parser.create_parsed_matches(
                eesl_tournament_id, self.service
            )

        return router
