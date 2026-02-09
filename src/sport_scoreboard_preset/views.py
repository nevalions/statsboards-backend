from typing import Annotated

from fastapi import Depends, HTTPException

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.dependencies import SportScoreboardPresetService
from src.core.models import SportScoreboardPresetDB

from ..logging_config import get_logger
from .schemas import (
    SportScoreboardPresetSchema,
    SportScoreboardPresetSchemaCreate,
    SportScoreboardPresetSchemaUpdate,
)


class SportScoreboardPresetAPIRouter(
    BaseRouter[
        SportScoreboardPresetSchema,
        SportScoreboardPresetSchemaCreate,
        SportScoreboardPresetSchemaUpdate,
    ]
):
    def __init__(self):
        super().__init__(
            "/api/sport-scoreboard-presets",
            ["sport-scoreboard-presets"],
            None,
        )
        self.logger = get_logger("SportScoreboardPresetAPIRouter", self)
        self.logger.debug("Initialized SportScoreboardPresetAPIRouter")

    def route(self):
        router = super().route()

        @router.get(
            "/",
            response_model=list[SportScoreboardPresetSchema],
        )
        async def get_all_presets_endpoint(
            sport_scoreboard_preset_service: SportScoreboardPresetService,
        ):
            self.logger.debug("Get all sport scoreboard presets endpoint")
            presets = await sport_scoreboard_preset_service.get_all_elements()
            return [SportScoreboardPresetSchema.model_validate(s) for s in presets]

        @router.post(
            "/",
            response_model=SportScoreboardPresetSchema,
        )
        async def create_preset_endpoint(
            item: SportScoreboardPresetSchemaCreate,
            sport_scoreboard_preset_service: SportScoreboardPresetService,
        ):
            self.logger.debug(f"Create sport scoreboard preset endpoint got data: {item}")
            new_ = await sport_scoreboard_preset_service.create(item)
            return SportScoreboardPresetSchema.model_validate(new_)

        @router.put(
            "/{item_id}/",
            response_model=SportScoreboardPresetSchema,
        )
        async def update_preset_endpoint(
            item_id: int,
            item: SportScoreboardPresetSchemaUpdate,
            sport_scoreboard_preset_service: SportScoreboardPresetService,
        ):
            self.logger.debug(f"Update sport scoreboard preset endpoint id:{item_id} data: {item}")
            update_ = await sport_scoreboard_preset_service.update(
                item_id,
                item,
            )
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Sport scoreboard preset {item_id} not found"
                )
            return SportScoreboardPresetSchema.model_validate(update_)

        @router.get(
            "/id/{item_id}/",
            response_model=SportScoreboardPresetSchema,
        )
        async def get_preset_by_id_endpoint(
            item_id: int,
            sport_scoreboard_preset_service: SportScoreboardPresetService,
        ):
            self.logger.debug(f"Getting sport scoreboard preset by id: {item_id} endpoint")
            item = await sport_scoreboard_preset_service.get_by_id(item_id)
            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sport scoreboard preset id:{item_id} not found",
                )
            return SportScoreboardPresetSchema.model_validate(item)

        @router.get("/id/{preset_id}/sports")
        async def sports_by_preset_endpoint(
            preset_id: int,
            sport_scoreboard_preset_service: SportScoreboardPresetService,
        ):
            self.logger.debug(f"Get sports by sport scoreboard preset id:{preset_id} endpoint")
            return await sport_scoreboard_preset_service.get_sports_by_preset(preset_id)

        @router.delete(
            "/id/{model_id}",
            summary="Delete sport scoreboard preset",
            description="Delete a sport scoreboard preset by ID. Requires admin role.",
            responses={
                200: {"description": "Sport scoreboard preset deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Sport scoreboard preset not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_preset_endpoint(
            model_id: int,
            _: Annotated[SportScoreboardPresetDB, Depends(require_roles("admin"))],
            sport_scoreboard_preset_service: SportScoreboardPresetService,
        ):
            self.logger.debug(f"Delete sport scoreboard preset endpoint id:{model_id}")
            await sport_scoreboard_preset_service.delete(model_id)
            return {"detail": f"Sport scoreboard preset {model_id} deleted successfully"}

        return router


api_sport_scoreboard_preset_router = SportScoreboardPresetAPIRouter().route()
