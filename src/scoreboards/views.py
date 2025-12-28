from fastapi import Depends, status

from src.core import BaseRouter, db
from .db_services import ScoreboardServiceDB
from .schemas import ScoreboardSchema, ScoreboardSchemaCreate, ScoreboardSchemaUpdate

from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse

from ..logging_config import get_logger, setup_logging

setup_logging()


class ScoreboardAPIRouter(
    BaseRouter[
        ScoreboardSchema,
        ScoreboardSchemaCreate,
        ScoreboardSchemaUpdate,
    ]
):
    def __init__(self, service: ScoreboardServiceDB):
        super().__init__("/api/scoreboards", ["scoreboards"], service)
        self.logger = get_logger("backend_logger_ScoreboardAPIRouter", self)
        self.logger.debug(f"Initialized ScoreboardAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=ScoreboardSchema,
        )
        async def create_scoreboard(scoreboard_data: ScoreboardSchemaCreate):
            self.logger.debug(f"Create scoreboard endpoint got data: {scoreboard_data}")
            try:
                new_scoreboard = await self.service.create_scoreboard(scoreboard_data)
                return ScoreboardSchema.model_validate(new_scoreboard)
            except Exception as ex:
                self.logger.error(
                    f"Error creating scoreboard with data: {scoreboard_data} {ex}",
                    exc_info=True,
                )

        @router.put(
            "/{item_id}/",
            response_model=ScoreboardSchema,
        )
        async def update_scoreboard_(
            item_id: int,
            item: ScoreboardSchemaUpdate,
        ):
            self.logger.debug(f"Update scoreboard endpoint id:{item_id} data: {item}")
            try:
                scoreboard_update = await self.service.update_scoreboard(
                    item_id,
                    item,
                )

                if scoreboard_update is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Scoreboard id({item_id}) not found",
                    )
                return scoreboard_update
            except Exception as ex:
                self.logger.error(
                    f"Error updating scoreboard with data: {item} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=409,
                    detail=f"Error updating scoreboard with data",
                )

        @router.put(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def update_scoreboard_by_id(
            item_id: int,
            item=Depends(update_scoreboard_),
        ):
            self.logger.debug(f"Update scoreboard endpoint by ID")
            if item:
                return {
                    "content": ScoreboardSchema.model_validate(item).model_dump(),
                    "status_code": status.HTTP_200_OK,
                    "success": True,
                }

            raise HTTPException(
                status_code=404,
                detail=f"Scoreboard id:{item_id} not found",
            )

        @router.get(
            "/match/id/{match_id}",
            response_model=ScoreboardSchema,
        )
        async def get_scoreboard_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get scoreboard by match id: {match_id} endpoint")
            scoreboard = await self.service.get_scoreboard_by_match_id(value=match_id)
            if scoreboard is None:
                self.logger.warning(f"No scoreboard found for match id: {match_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Scoreboard match id({match_id}) not found",
                )
            return ScoreboardSchema.model_validate(scoreboard)

        @router.get(
            "/matchdata/id/{matchdata_id}",
            response_model=ScoreboardSchema,
        )
        async def get_scoreboard_by_matchdata_id_endpoint(matchdata_id: int):
            self.logger.debug(
                f"Get scoreboard by matchdata id: {matchdata_id} endpoint"
            )
            scoreboard = await self.service.get_scoreboard_by_matchdata_id(matchdata_id)
            if scoreboard is None:
                self.logger.warning(
                    f"No scoreboard found for matchdata id: {matchdata_id}"
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Scoreboard match id({matchdata_id}) not found",
                )
            return ScoreboardSchema.model_validate(scoreboard)

        """triggers for sse process, now we use websocket"""
        # @router.get("/matchdata/id/{match_data_id}/events/scoreboard_data/")
        # async def sse_scoreboard_data_endpoint(match_data_id: int):
        #     print("SSE Scoreboard Starts")
        #     scoreboard = await self.service.get_scoreboard_by_matchdata_id(
        #         match_data_id
        #     )
        #     print(scoreboard)
        #     # scoreboard = await self.service.get_scoreboard_by_match_id(5)
        #     print(scoreboard)
        #     if scoreboard:
        #         print(scoreboard)
        #         return StreamingResponse(
        #             self.service.event_generator_get_scoreboard_data(scoreboard.id),
        #             media_type="text/event-stream",
        #         )
        #     else:
        #         raise HTTPException(
        #             status_code=404,
        #             detail=f"Scoreboard match data id({match_data_id}) " f"not found",
        #         )

        # def create_directories():
        #     if not os.path.exists(static_path):
        #         os.makedirs(static_path)
        #     logos_path = os.path.join(static_path, "logos")
        #     if not os.path.exists(logos_path):
        #         os.makedirs(logos_path)

        # @router.post(
        #     "/api/change_logo/{team}",
        #     response_class=JSONResponse,
        # )
        # async def change_logo(team: str, logo: UploadFile = File(...)):
        #     create_directories()
        #
        #     if logo:
        #         file_ext = logo.filename.split(".")[-1]
        #
        #         # Ensure the 'static' folder exists
        #         if not os.path.exists(static_path):
        #             os.makedirs("static")
        #
        #         # Save the uploaded logo file
        #         logo_path = os.path.join(
        #             static_path,
        #             f'logos/{teams_data[team]["name"]}_new.{file_ext}',
        #         )
        #         print(logo_path)
        #         with open(logo_path, "wb") as f:
        #             f.write(logo.file.read())
        #
        #         # Update the team's logo path in the teams_data dictionary
        #         teams_data[team][
        #             "logo"
        #         ] = f'static/logos/{teams_data[team]["name"]}_new.{file_ext}'
        #
        #         await trigger_update()
        #         return {"success": True}
        #     else:
        #         return {
        #             "success": False,
        #             "error": "No logo file provided",
        #         }

        return router


api_scoreboards_router = ScoreboardAPIRouter(ScoreboardServiceDB(db)).route()
