from typing import List

from fastapi import HTTPException, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import MatchServiceDB
from .shemas import (
    MatchSchemaCreate,
    MatchSchemaUpdate,
    MatchSchema,
    MatchDataScoreboardSchemaCreate,
)
from src.core.config import scoreboard_template_path, match_template_path
from ..matchdata.db_services import MatchDataServiceDB
from ..matchdata.schemas import MatchDataSchemaCreate
from ..scoreboards.db_services import ScoreboardServiceDB
from ..scoreboards.shemas import ScoreboardSchemaCreate

scoreboard_templates = Jinja2Templates(directory=scoreboard_template_path)
match_templates = Jinja2Templates(directory=match_template_path)


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
        async def create_match_endpoint(
            match: MatchSchemaCreate,
        ):
            new_match = await self.service.create_or_update_match(match)
            return new_match.__dict__

        @router.post(
            "/create_with_full_data/",
            response_model=MatchDataScoreboardSchemaCreate,
        )
        async def create_match_with_full_data_endpoint(
            data: MatchDataScoreboardSchemaCreate,
        ):
            match_db_service = MatchDataServiceDB(db)
            scoreboard_db_service = ScoreboardServiceDB(db)

            # Create all
            new_match = await self.service.create_or_update_match(data.match)

            data.match_data.match_id = data.scoreboard.match_id = new_match.id
            new_match_data = await match_db_service.create_match_data(data.match_data)
            new_scoreboard = await scoreboard_db_service.create_scoreboard(
                data.scoreboard
            )

            # Return the created objects
            return {
                "match": new_match,
                "match_data": new_match_data,
                "scoreboard": new_scoreboard,
            }

        @router.get("/get_match_full_data_schemas/")
        async def get_match_full_data_schemas_endpoint():
            match_schema = MatchSchemaCreate.model_json_schema()
            match_data_schema = MatchDataSchemaCreate.model_json_schema()
            scoreboard_schema = ScoreboardSchemaCreate.model_json_schema()

            # print(list(match_schema["properties"].keys()))

            return {
                "match": list(match_schema["properties"].keys()),
                "match_data": list(match_data_schema["properties"].keys()),
                "scoreboard": list(scoreboard_schema["properties"].keys()),
            }

        @router.put(
            "/",
            response_model=MatchSchema,
        )
        async def update_match_endpoint(
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
            "/eesl_id/{eesl_id}/",
            response_model=MatchSchema,
        )
        async def get_match_by_eesl_id_endpoint(eesl_id: int):
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
        async def get_match_teams_by_match_id_endpoint(match_id: int):
            return await self.service.get_teams_by_match(match_id)

        @router.get(
            "/id/{match_id}/match_data/",
        )
        async def get_match_data_by_match_id_endpoint(match_id: int):
            return await self.service.get_matchdata_by_match(match_id)

        @router.get(
            "/id/{match_id}/scoreboard_data/",
        )
        async def get_match_scoreboard_by_match_id_endpoint(match_id: int):
            return await self.service.get_scoreboard_by_match(match_id)

        @router.get("/all/data/", response_class=JSONResponse)
        async def all_matches_data_endpoint_endpoint(
            all_matches: List = Depends(
                self.service.get_all_elements
            ),  # Fetch all matches
        ):
            match_data_service_db = MatchDataServiceDB(db)
            # print(all_matches)
            all_match_data = []
            for match in all_matches:
                match_id = match.id
                match_teams_data = await get_match_teams_by_match_id_endpoint(match_id)
                match_data = await get_match_data_by_match_id_endpoint(match_id)

                if match_data is None:
                    match_data_schema = MatchDataSchemaCreate(
                        match_id=match_id,
                    )  # replace the arguments with real values
                    match_data = await match_data_service_db.create_match_data(
                        match_data_schema
                    )

                all_match_data.append(
                    {
                        "match_id": match_id,
                        "status_code": status.HTTP_200_OK,
                        "teams_data": match_teams_data,
                        "match_data": match_data.__dict__,
                    },
                )
            return all_match_data

        @router.get(
            "/id/{match_id}/data/",
            response_class=JSONResponse,
        )
        async def match_data_endpoint(
            request: Request,
            match_id: int,
            match_teams_data=Depends(get_match_teams_by_match_id_endpoint),
            match_data=Depends(get_match_data_by_match_id_endpoint),
        ):
            return (
                {
                    "status_code": status.HTTP_200_OK,
                    "teams_data": match_teams_data,
                    "match_data": match_data.__dict__,
                },
            )

        @router.get(
            "/id/{match_id}/scoreboard/full_data/",
            response_class=JSONResponse,
        )
        async def full_match_data_endpoint(
            request: Request,
            match_id: int,
            match_teams_data=Depends(get_match_teams_by_match_id_endpoint),
            match_data=Depends(get_match_data_by_match_id_endpoint),
            scoreboard_data=Depends(get_match_scoreboard_by_match_id_endpoint),
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
            "/all/",
            response_class=JSONResponse,
        )
        async def get_all_matches_endpoint(request: Request):
            template = match_templates.TemplateResponse(
                name="/display/all-matches.html",
                context={
                    "request": request,
                },
                status_code=200,
            )
            return template

        @router.get(
            "/id/{match_id}/scoreboard/",
            response_class=JSONResponse,
        )
        async def edit_match_data_endpoint(
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

        @router.get(
            "/id/{match_id}/scoreboard/hd/",
            response_class=JSONResponse,
        )
        async def display_fullhd_match_data_endpoint(
            request: Request,
            match_id: int,
        ):
            template = scoreboard_templates.TemplateResponse(
                name="/display/score-fullhd.html",
                context={
                    "request": request,
                },
                status_code=200,
            )
            return template

        return router


api_match_router = MatchRouter(MatchServiceDB(db)).route()
