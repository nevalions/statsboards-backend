import os

from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

# Set the template and static folders
parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
more_parent_path = os.path.dirname(parent_path)
one_more_parent_path = os.path.dirname(more_parent_path)
template_path = os.path.join(one_more_parent_path, "statsboards-frontend/frontend")
scoreboard_template_path = os.path.join(template_path, "scoreboards")
static_path = os.path.join(template_path, "static")
static_path_scoreboard = os.path.join(static_path, "scoreboards")
print(parent_path, one_more_parent_path, template_path, static_path)


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


class Settings(BaseSettings):
    # api_v1_prefix: str = "/api/v1"
    db: DbSettings = DbSettings()
    db_echo: bool = False


settings = Settings()
# print(str(settings.db.db_url))
