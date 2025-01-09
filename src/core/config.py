import os
import logging

from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi.templating import Jinja2Templates

from src.logging_config import setup_logging

load_dotenv()
setup_logging()
logger = logging.getLogger("backend_logger_config")

# Set the template and static folders
parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
more_parent_path = os.path.dirname(parent_path)
one_more_parent_path = os.path.dirname(more_parent_path)
template_path = os.path.join(one_more_parent_path, "statsboards-frontend/frontend")
# scoreboard_template_path = os.path.join(template_path, "scoreboards")
# match_template_path = os.path.join(template_path, "matches")
static_main_path = os.path.join(more_parent_path, "static")
uploads_path = os.path.join(static_main_path, "uploads")

static_path = os.path.join(template_path, "static")
# static_path_scoreboard = os.path.join(static_path, "scoreboards")

templates = Jinja2Templates(directory=template_path)

logger.info(f"parent_path: {parent_path}")
logger.info(f"one_more_parent_path: {one_more_parent_path}")
logger.info(f"template_path: {template_path}")
logger.info(f"static_path: {static_path}")
logger.info(f"static_main_path: {static_main_path}")
logger.info(f"uploads_path: {uploads_path}")


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_")
    host: str
    user: str
    password: str
    name: str
    port: int

    @property
    def db_url(self) -> PostgresDsn:
        # print(self.host, self.user, self.password, self.name)
        url = str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                path=self.name,
            )
        )
        return url

    def db_url_websocket(self) -> PostgresDsn:
        # print(self.host, self.user, self.password, self.name)
        url = str(
            PostgresDsn.build(
                scheme="postgresql",
                username=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                path=self.name,
            )
        )
        return url


class TestDbSettings(DbSettings):
    model_config = SettingsConfigDict(env_file=".env.test", env_prefix="DB_")


class Settings(BaseSettings):
    # api_v1_prefix: str = "/api/v1"
    db: DbSettings = DbSettings()
    db_echo: bool = False


settings = Settings()
# print(str(settings.db.db_url))
