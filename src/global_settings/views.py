from typing import Annotated

from fastapi import Depends, HTTPException

from src.auth.dependencies import require_roles
from src.core import BaseRouter, db
from src.core.models import UserDB

from ..logging_config import get_logger
from .db_services import GlobalSettingServiceDB
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
    def __init__(self, service: GlobalSettingServiceDB):
        super().__init__(
            "/api/settings",
            ["settings"],
            service,
        )
        self.logger = get_logger("backend_logger_GlobalSettingAPIRouter", self)
        self.logger.debug("Initialized GlobalSettingAPIRouter")

    def route(self):
        router = super().route()

        @router.get("/grouped")
        async def get_all_settings_grouped():
            """Get all settings grouped by category for frontend."""
            self.logger.debug("Get all settings grouped by category")
            grouped = await self.service.get_all_grouped()
            return grouped

        @router.get("/category/{category}")
        async def get_settings_by_category(category: str):
            """Get all settings in a specific category."""
            self.logger.debug(f"Get settings by category:{category}")
            settings = await self.service.get_all_by_category(category)
            return [GlobalSettingSchema.model_validate(s) for s in settings]

        @router.get("/value/{key}", response_model=GlobalSettingValueSchema)
        async def get_setting_value(key: str):
            """Get a specific setting value with type conversion."""
            self.logger.debug(f"Get setting value for key:{key}")
            value = await self.service.get_value(key)
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
            item: GlobalSettingSchemaCreate,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ):
            """Create a new global setting (admin only)."""
            self.logger.debug(f"Create setting endpoint got data: {item}")
            new_ = await self.service.create(item)
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
            item_id: int,
            item: GlobalSettingSchemaUpdate,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ):
            """Update a global setting (admin only)."""
            self.logger.debug(f"Update setting endpoint id:{item_id} data: {item}")
            update_ = await self.service.update(
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
            model_id: int,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ):
            """Delete a global setting (admin only)."""
            self.logger.debug(f"Delete setting endpoint id:{model_id}")
            await self.service.delete(model_id)
            return {"detail": f"Setting {model_id} deleted successfully"}

        return router


api_global_setting_router = GlobalSettingAPIRouter(GlobalSettingServiceDB(db)).route()
