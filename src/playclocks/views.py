from fastapi import (
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core import BaseRouter, db

from ..logging_config import get_logger
from .db_services import PlayClockServiceDB
from .schemas import PlayClockSchema, PlayClockSchemaCreate, PlayClockSchemaUpdate


class PlayClockAPIRouter(
    BaseRouter[
        PlayClockSchema,
        PlayClockSchemaCreate,
        PlayClockSchemaUpdate,
    ]
):
    def __init__(self, service: PlayClockServiceDB):
        super().__init__(
            "/api/playclock",
            ["playclock"],
            service,
        )
        self.logger = get_logger("backend_logger_PlayClockAPIRouter", self)
        self.logger.debug("Initialized PlayClockAPIRouter")

    def route(self):
        router = super().route()

        # Playclock backend
        @router.post(
            "/",
            response_model=PlayClockSchema,
        )
        async def create_playclock_endpoint(playclock_data: PlayClockSchemaCreate):
            self.logger.debug(f"Create playclock endpoint got data: {playclock_data}")
            try:
                new_playclock = await self.service.create(playclock_data)
                return PlayClockSchema.model_validate(new_playclock)
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(
                    f"Error creating playclock with data: {playclock_data} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Database error creating playclock",
                )
            except Exception as ex:
                self.logger.error(
                    f"Error creating playclock with data: {playclock_data} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error creating playclock",
                )

        @router.put(
            "/{item_id}/",
            response_model=PlayClockSchema,
        )
        async def update_playclock_(
            item_id: int,
            item: PlayClockSchemaUpdate,
        ):
            self.logger.debug(f"Update playclock endpoint id:{item_id} data: {item}")
            try:
                playclock_update = await self.service.update(
                    item_id,
                    item,
                )
                return playclock_update
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error updating playclock with data: {item} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error updating playclock",
                )

        @router.put(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def update_playclock_by_id(
            item_id: int,
            item=Depends(update_playclock_),
        ):
            self.logger.debug("Update playclock endpoint by ID")
            if item:
                return {
                    "content": PlayClockSchema.model_validate(item).model_dump(),
                    "status_code": status.HTTP_200_OK,
                    "success": True,
                }

            raise HTTPException(
                status_code=404,
                detail=f"Playclock id:{item_id} not found",
            )

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_playclock_by_id(
            item=Depends(self.service.get_by_id),
        ):
            self.logger.debug("Get playclock endpoint by ID")
            if item is None:
                raise HTTPException(status_code=404, detail="Playclock not found")
            return self.create_response(
                item,
                f"Playclock ID:{item.id}",
                "playclock",
            )

        @router.put(
            "/id/{item_id}/running/{sec}/",
            response_class=JSONResponse,
        )
        async def start_playclock_endpoint(
            background_tasks: BackgroundTasks,
            item_id: int,
            sec: int,
        ):
            self.logger.debug(f"Start playclock endpoint with id: {item_id}")
            try:
                item_status = "running"
                item = await self.service.get_by_id(item_id)
                present_playclock_status = item.playclock_status

                await self.service.enable_match_data_clock_queues(item_id)
                if present_playclock_status != "running":
                    await self.service.update(
                        item_id,
                        PlayClockSchemaUpdate(
                            playclock=sec,
                            playclock_status=item_status,
                        ),
                    )

                if not self.service.disable_background_tasks:
                    self.logger.debug("Start playclock background task, loop decrement")
                    await self.service.decrement_playclock(
                        background_tasks,
                        item_id,
                    )

                return self.create_response(
                    item,
                    f"Playclock ID:{item_id} {item_status}",
                )
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(
                    f"Error starting playclock with id: {item_id} {ex}", exc_info=True
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error starting playclock with id {item_id}",
                )
            except Exception as ex:
                self.logger.error(f"Error starting playclock with id: {item_id} {ex}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error starting playclock",
                )

        @router.put(
            "/id/{item_id}/{item_status}/{sec}/",
            response_class=JSONResponse,
        )
        async def reset_playclock_endpoint(
            item_id: int,
            item_status: str = Path(
                ...,
                examples=["stopped"],
            ),
            sec: int = Path(
                ...,
                description="Seconds",
                examples=[25],
            ),
        ):
            self.logger.debug(f"Resetting playclock endpoint with id: {item_id}")
            try:
                updated = await self.service.update(
                    item_id,
                    PlayClockSchemaUpdate(
                        playclock=sec,
                        playclock_status=item_status,
                    ),
                )

                return self.create_response(
                    updated,
                    f"Playclock {item_status}",
                )
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(
                    f"Error resetting playclock with id: {item_id} {ex}", exc_info=True
                )
                raise HTTPException(
                    status_code=500,
                    detail="Database error resetting playclock",
                )
            except Exception as ex:
                self.logger.error(f"Error resetting playclock with id: {item_id} {ex}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error resetting playclock",
                )

        @router.put(
            "/id/{item_id}/stopped/",
            response_class=JSONResponse,
        )
        async def reset_playclock_stopped_endpoint(item_id: int):
            self.logger.debug(
                f"Resetting playclock to stopped endpoint with id: {item_id}"
            )
            try:
                updated = await self.service.update_with_none(
                    item_id,
                    PlayClockSchemaUpdate(
                        playclock=None,
                        playclock_status="stopped",
                    ),
                )

                return self.create_response(
                    updated,
                    "Playclock stopped",
                )
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(
                    f"Error resetting playclock with id: {item_id} {ex}", exc_info=True
                )
                raise HTTPException(
                    status_code=500,
                    detail="Database error resetting playclock",
                )
            except Exception as ex:
                self.logger.error(f"Error resetting playclock with id: {item_id} {ex}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error resetting playclock",
                )

        return router


api_playclock_router = PlayClockAPIRouter(PlayClockServiceDB(db)).route()
