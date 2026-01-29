from typing import Annotated, List

from fastapi import Depends, HTTPException

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.dependencies import GlobalSettingService
from src.core.models import UserDB
from src.core.service_registry import get_service_registry
from src.seasons.schemas import SeasonSchema, SeasonSchemaCreate, SeasonSchemaUpdate

from ..logging_config import get_logger
from .schemas import (
    GlobalSettingSchema,
    GlobalSettingSchemaCreate,
    GlobalSettingSchemaUpdate,
    GlobalSettingValueSchema,
)


class GlobalSettingAPIRouter(
    BaseRouter[
        GlobalSettingSchema,
        GlobalSettingSchemaCreate,
        GlobalSettingSchemaUpdate,
    ]
):
    def __init__(self):
        super().__init__(
            "/api/settings",
            ["settings"],
            None,
        )
        self.logger = get_logger("GlobalSettingAPIRouter", self)
        self.logger.debug("Initialized GlobalSettingAPIRouter")

    def route(self):
        router = super().route()

        @router.get("/grouped")
        async def get_all_settings_grouped(global_setting_service: GlobalSettingService):
            """Get all settings grouped by category for frontend."""
            self.logger.debug("Get all settings grouped by category")
            grouped = await global_setting_service.get_all_grouped()
            return grouped

        @router.get("/category/{category}")
        async def get_settings_by_category(
            global_setting_service: GlobalSettingService, category: str
        ):
            """Get all settings in a specific category."""
            self.logger.debug(f"Get settings by category:{category}")
            settings = await global_setting_service.get_all_by_category(category)
            return [GlobalSettingSchema.model_validate(s) for s in settings]

        @router.get("/value/{key}", response_model=GlobalSettingValueSchema)
        async def get_setting_value(key: str):
            """Get a specific setting value with type conversion."""
            self.logger.debug(f"Get setting value for key:{key}")
            # Use service registry to get fresh service instance with correct database
            registry = get_service_registry()
            service = registry.get("global_setting")
            value = await service.get_value(key)
            if value is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Setting '{key}' not found",
                )
            return GlobalSettingValueSchema(value=str(value))

        @router.post(
            "/",
            response_model=GlobalSettingSchema,
            summary="Create a new global setting",
            description="Create a new global setting. Requires admin role.",
            responses={
                201: {"description": "Setting created successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                422: {"description": "Validation error"},
            },
        )
        async def create_setting_endpoint(
            global_setting_service: GlobalSettingService,
            item: GlobalSettingSchemaCreate,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ):
            """Create a new global setting (admin only)."""
            self.logger.debug(f"Create setting endpoint got data: {item}")
            new_ = await global_setting_service.create(item)
            return GlobalSettingSchema.model_validate(new_)

        @router.put(
            "/{item_id}/",
            response_model=GlobalSettingSchema,
            summary="Update a global setting",
            description="Update a global setting by ID. Requires admin role.",
            responses={
                200: {"description": "Setting updated successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Setting not found"},
                422: {"description": "Validation error"},
            },
        )
        async def update_setting_endpoint(
            global_setting_service: GlobalSettingService,
            item_id: int,
            item: GlobalSettingSchemaUpdate,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ):
            """Update a global setting (admin only)."""
            self.logger.debug(f"Update setting endpoint id:{item_id} data: {item}")
            update_ = await global_setting_service.update(
                item_id,
                item,
            )
            if update_ is None:
                raise HTTPException(status_code=404, detail=f"Setting {item_id} not found")
            return GlobalSettingSchema.model_validate(update_)

        @router.delete(
            "/id/{model_id}",
            summary="Delete a global setting",
            description="Delete a global setting by ID. Requires admin role.",
            responses={
                200: {"description": "Setting deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Setting not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_setting_endpoint(
            global_setting_service: GlobalSettingService,
            model_id: int,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ):
            """Delete a global setting (admin only)."""
            self.logger.debug(f"Delete setting endpoint id:{model_id}")
            await global_setting_service.delete(model_id)
            return {"detail": f"Setting {model_id} deleted successfully"}

        @router.post(
            "/seasons/",
            response_model=SeasonSchema,
            summary="Create a new season",
            description="Create a new season through settings API.",
            responses={
                200: {"description": "Season created successfully"},
                422: {"description": "Validation error"},
            },
        )
        async def create_season_endpoint(
            global_setting_service: GlobalSettingService, item: SeasonSchemaCreate
        ):
            """Create a new season through settings API."""
            self.logger.debug(f"Create season endpoint got data: {item}")
            new_ = await global_setting_service.create_season(item)
            return new_

        @router.put(
            "/seasons/{item_id}/",
            response_model=SeasonSchema,
            summary="Update a season",
            description="Update a season by ID through settings API.",
            responses={
                200: {"description": "Season updated successfully"},
                404: {"description": "Season not found"},
                422: {"description": "Validation error"},
            },
        )
        async def update_season_endpoint(
            global_setting_service: GlobalSettingService,
            item_id: int,
            item: SeasonSchemaUpdate,
        ):
            """Update a season through settings API."""
            self.logger.debug(f"Update season endpoint id:{item_id} data: {item}")
            update_ = await global_setting_service.update_season(item_id, item)
            if update_ is None:
                raise HTTPException(status_code=404, detail=f"Season {item_id} not found")
            return update_

        @router.get(
            "/seasons/id/{item_id}/",
            response_model=SeasonSchema,
            summary="Get a season by ID",
            description="Get a season by ID through settings API.",
            responses={
                200: {"description": "Season retrieved successfully"},
                404: {"description": "Season not found"},
            },
        )
        async def get_season_by_id_endpoint(
            global_setting_service: GlobalSettingService, item_id: int
        ):
            """Get a season by ID through settings API."""
            self.logger.debug(f"Get season by id endpoint: {item_id}")
            season = await global_setting_service.get_season_by_id(item_id)
            if season is None:
                raise HTTPException(status_code=404, detail=f"Season {item_id} not found")
            return season

        @router.delete(
            "/seasons/id/{model_id}",
            summary="Delete a season",
            description="Delete a season by ID through settings API.",
            responses={
                200: {"description": "Season deleted successfully"},
                404: {"description": "Season not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_season_endpoint(
            global_setting_service: GlobalSettingService, model_id: int
        ):
            """Delete a season through settings API."""
            self.logger.debug(f"Delete season endpoint id:{model_id}")
            await global_setting_service.delete_season(model_id)
            return {"detail": f"Season {model_id} deleted successfully"}

        @router.get(
            "/seasons/",
            response_model=List[SeasonSchema],
            summary="Get all seasons",
            description="Get all seasons ordered by year through settings API.",
            responses={
                200: {"description": "Seasons retrieved successfully"},
            },
        )
        async def get_all_seasons_endpoint(global_setting_service: GlobalSettingService):
            """Get all seasons through settings API ordered by year."""
            self.logger.debug("Get all seasons endpoint")
            seasons = await global_setting_service.get_all_seasons()
            return seasons

        return router


api_global_setting_router = GlobalSettingAPIRouter().route()
