from fastapi import HTTPException, Depends, status
from fastapi.templating import Jinja2Templates

from src.core import BaseRouter, db
from src.core.config import static_path_scoreboard, scoreboard_template_path
from .db_services import ScoreboardServiceDB
from .shemas import ScoreboardSchema, ScoreboardSchemaCreate, ScoreboardSchemaUpdate

from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse

scoreboard_templates = Jinja2Templates(directory=scoreboard_template_path)


# Team backend
class ScoreboardRouter(
    BaseRouter[
        ScoreboardSchema,
        ScoreboardSchemaCreate,
        ScoreboardSchemaUpdate,
    ]
):
    def __init__(self, service: ScoreboardServiceDB):
        super().__init__("/api/scoreboards", ["scoreboards"], service)

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=ScoreboardSchema,
        )
        async def create_scoreboard(scoreboard: ScoreboardSchemaCreate):
            new_scoreboard = await self.service.create_scoreboard(scoreboard)
            return new_scoreboard.__dict__

        @router.put(
            "/{item_id}/",
            response_model=ScoreboardSchema,
        )
        async def update_scoreboard_(
            item_id: int,
            item: ScoreboardSchemaUpdate,
        ):
            update_ = await self.service.update_scoreboard(
                item_id,
                item,
            )
            if update_:
                return update_

            raise HTTPException(
                status_code=404,
                detail=f"Scoreboard id:{item_id} not found",
            )

        @router.put(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def update_scoreboard_by_id(
            item_id: int,
            item=Depends(update_scoreboard_),
        ):
            if item:
                return {
                    "content": item.__dict__,
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
            scoreboard = await self.service.get_scoreboard_by_match_id(value=match_id)
            if scoreboard is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Scoreboard match id({match_id}) " f"not found",
                )
            return scoreboard.__dict__

        @router.get(
            "/matchdata/id/{matchdata_id}",
            response_model=ScoreboardSchema,
        )
        async def get_scoreboard_by_matchdata_id_endpoint(matchdata_id: int):
            scoreboard = await self.service.get_scoreboard_by_matchdata_id(matchdata_id)
            if scoreboard is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Scoreboard match id({matchdata_id}) " f"not found",
                )
            return scoreboard.__dict__

        @router.get("/matchdata/id/{match_data_id}/events/scoreboard_data/")
        async def sse_scoreboard_data_endpoint(match_data_id: int):
            print("SSE Scoreboard Starts")
            scoreboard = await self.service.get_scoreboard_by_matchdata_id(
                match_data_id
            )
            print(scoreboard)
            if scoreboard:
                print(scoreboard)
                return StreamingResponse(
                    self.service.event_generator_get_scoreboard_data(scoreboard.id),
                    media_type="text/event-stream",
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Scoreboard match data id({match_data_id}) " f"not found",
                )

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


api_scoreboards_router = ScoreboardRouter(ScoreboardServiceDB(db)).route()
