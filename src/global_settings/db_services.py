import json
from typing import Any

from sqlalchemy import asc, select

from src.core.decorators import handle_service_exceptions
from src.core.models import BaseServiceDB, GlobalSettingDB, SeasonDB
from src.core.models.base import Database
from src.seasons.db_services import SeasonServiceDB
from src.seasons.schemas import SeasonSchema, SeasonSchemaCreate, SeasonSchemaUpdate

from ..logging_config import get_logger
from .schemas import GlobalSettingSchemaCreate, GlobalSettingSchemaUpdate

ITEM = "GLOBAL_SETTING"


class GlobalSettingServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(
            database,
            model=GlobalSettingDB,
        )
        self.season_service = SeasonServiceDB(database)
        self.logger = get_logger("GlobalSettingServiceDB", self)
        self.logger.debug("Initialized GlobalSettingServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(self, item: GlobalSettingSchemaCreate) -> GlobalSettingDB:
        self.logger.debug(f"Create {ITEM}:{item}")
        return await super().create(item)

    @handle_service_exceptions(item_name=ITEM, operation="updating", reraise_not_found=True)
    async def update(
        self,
        item_id: int,
        item: GlobalSettingSchemaUpdate,
        **kwargs,
    ) -> GlobalSettingDB:
        self.logger.debug(f"Update {ITEM} with id:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get setting value with automatic type conversion.

        Args:
            key: Setting key
            default: Default value if setting not found

        Returns:
            Parsed value according to value_type, or default if not found
        """
        self.logger.debug(f"Get {ITEM} value for key:{key}")
        async with self.db.get_session_maker()() as session:
            stmt = select(GlobalSettingDB).where(GlobalSettingDB.key == key)
            result = await session.execute(stmt)
            setting = result.scalar_one_or_none()

            if setting is None:
                self.logger.debug(f"{ITEM} not found for key:{key}, returning default")
                return default

            return self._parse_value(setting.value, setting.value_type)

    async def get_all_by_category(self, category: str) -> list[GlobalSettingDB]:
        """Get all settings in a specific category.

        Args:
            category: Category name

        Returns:
            List of settings in the category
        """
        self.logger.debug(f"Get {ITEM}s by category:{category}")
        async with self.db.get_session_maker()() as session:
            stmt = (
                select(GlobalSettingDB)
                .where(GlobalSettingDB.category == category)
                .order_by(GlobalSettingDB.key)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_all_grouped(self) -> dict[str, list[dict[str, Any]]]:
        """Get all settings grouped by category for frontend.

        Returns:
            Dictionary mapping categories to list of setting dicts
        """
        self.logger.debug(f"Get all {ITEM}s grouped by category")
        async with self.db.get_session_maker()() as session:
            stmt = select(GlobalSettingDB).order_by(GlobalSettingDB.category, GlobalSettingDB.key)
            result = await session.execute(stmt)
            settings = result.scalars().all()

        grouped = {}
        for setting in settings:
            category = setting.category or "general"
            if category not in grouped:
                grouped[category] = []

            grouped[category].append(
                {
                    "id": setting.id,
                    "key": setting.key,
                    "value": setting.value,
                    "value_type": setting.value_type,
                    "description": setting.description,
                    "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
                }
            )

        return grouped

    def _parse_value(self, value: str, value_type: str) -> Any:
        """Parse string value to appropriate Python type.

        Args:
            value: String value from database
            value_type: Type identifier ('string', 'int', 'bool', 'json')

        Returns:
            Parsed value
        """
        try:
            match value_type:
                case "string":
                    return value
                case "int":
                    return int(value)
                case "bool":
                    return value.lower() in ("true", "1", "yes", "on")
                case "json":
                    return json.loads(value)
                case _:
                    self.logger.warning(f"Unknown value_type:{value_type}, returning as string")
                    return value
        except (ValueError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to parse value '{value}' as type '{value_type}': {e}")
            return value

    def _serialize_value(self, value: Any, value_type: str) -> str:
        """Serialize Python value to string for database storage.

        Args:
            value: Python value
            value_type: Target type identifier ('string', 'int', 'bool', 'json')

        Returns:
            String representation for database
        """
        match value_type:
            case "string":
                return str(value)
            case "int":
                return str(int(value))
            case "bool":
                return "true" if bool(value) else "false"
            case "json":
                return json.dumps(value)
            case _:
                return str(value)

    async def create_season(self, item: SeasonSchemaCreate) -> SeasonSchema:
        """Create a new season through settings API."""
        self.logger.debug(f"Create season via settings: {item}")
        season = await self.season_service.create(item)
        return SeasonSchema.model_validate(season)

    async def update_season(
        self,
        item_id: int,
        item: SeasonSchemaUpdate,
    ) -> SeasonSchema | None:
        """Update a season through settings API."""
        self.logger.debug(f"Update season via settings id:{item_id} data: {item}")
        season = await self.season_service.update(item_id, item)
        if season is None:
            return None
        return SeasonSchema.model_validate(season)

    async def get_season_by_id(self, item_id: int) -> SeasonSchema | None:
        """Get a season by ID through settings API."""
        self.logger.debug(f"Get season via settings id:{item_id}")
        season = await self.season_service.get_by_id(item_id)
        if season is None:
            return None
        return SeasonSchema.model_validate(season)

    async def delete_season(self, item_id: int) -> None:
        """Delete a season through settings API."""
        self.logger.debug(f"Delete season via settings id:{item_id}")
        await self.season_service.delete(item_id)

    async def get_all_seasons(self) -> list[SeasonSchema]:
        """Get all seasons ordered by year."""
        self.logger.debug("Get all seasons via settings")
        async with self.db.get_session_maker()() as session:
            stmt = select(SeasonDB).order_by(asc(SeasonDB.year))
            result = await session.execute(stmt)
            seasons = result.scalars().all()
            return [SeasonSchema.model_validate(s) for s in seasons]
