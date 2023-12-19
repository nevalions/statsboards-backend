import asyncio

from fastapi import HTTPException, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

# from starlette.templating import Jinja2Templates

from src.core import BaseRouter, db
from .db_services import MatchServiceDB
from .shemas import MatchSchemaCreate, MatchSchemaUpdate, MatchSchema
from ..core.config import scoreboard_template_path

# from ..scoreboards.views import teams_data, game_data

scoreboard_templates = Jinja2Templates(directory=scoreboard_template_path)


# Match backend
class MatchRouter(
    BaseRouter[
        MatchSchema,
        MatchSchemaCreate,
        MatchSchemaUpdate,
    ]
):
    def __init__(self, service: MatchServiceDB):
        super().__init__(
            "/api/matches",
            ["matches"],
            service,
        )

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=MatchSchema,
        )
        async def create_match(
            match: MatchSchemaCreate,
        ):
            new_match = await self.service.create_or_update_match(match)
            return new_match.__dict__

        @router.put(
            "/",
            response_model=MatchSchema,
        )
        async def update_match(
            item_id: int,
            item: MatchSchemaUpdate,
        ):
            match_update = await self.service.update_match(item_id, item)

            if match_update is None:
                raise HTTPException(
                    status_code=404, detail=f"Match id({item_id}) " f"not found"
                )
            return match_update.__dict__

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=MatchSchema,
        )
        async def get_match_by_eesl_id(eesl_id: int):
            match = await self.service.get_match_by_eesl_id(value=eesl_id)
            if match is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Match eesl_id({eesl_id}) " f"not found",
                )
            return match.__dict__

        @router.get(
            "/id/{match_id}/teams/",
        )
        async def get_match_teams_by_match_id(match_id: int):
            return await self.service.get_teams_by_match(match_id)

        @router.get(
            "/id/{match_id}/match_data/",
        )
        async def get_match_data_by_match_id(match_id: int):
            return await self.service.get_matchdata_by_match(match_id)

        @router.get(
            "/id/{match_id}/scoreboard_data/",
        )
        async def get_match_scoreboard_by_match_id(match_id: int):
            return await self.service.get_scoreboard_by_match(match_id)

        @router.get(
            "/id/{match_id}/scoreboard/full_data/",
            response_class=JSONResponse,
        )
        async def index_json(
            request: Request,
            match_id: int,
            match_teams_data=Depends(get_match_teams_by_match_id),
            match_data=Depends(get_match_data_by_match_id),
            scoreboard_data=Depends(get_match_scoreboard_by_match_id),
        ):
            return (
                {
                    "status_code": status.HTTP_200_OK,
                    "teams_data": match_teams_data,
                    "match_data": match_data.__dict__,
                    "scoreboard_data": scoreboard_data.__dict__,
                },
            )

        @router.get(
            "/id/{match_id}/scoreboard/",
            response_class=JSONResponse,
        )
        async def index(
            request: Request,
            match_id: int,
        ):
            template = scoreboard_templates.TemplateResponse(
                name="/display/score-main.html",
                context={
                    "request": request,
                },
                status_code=200,
            )
            return template

        return router


api_match_router = MatchRouter(MatchServiceDB(db)).route()
