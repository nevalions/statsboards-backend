from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_prefix='DB_')
    host: str
    user: str
    password: str
    name: str
    port: int

    @property
    def db_url(self) -> PostgresDsn:
        # print(self.host, self.user, self.password, self.name)
        url = str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            path=self.name
        ))
        return url


class Settings(BaseSettings):

    # api_v1_prefix: str = "/api/v1"
    db: DbSettings = DbSettings()
    db_echo: bool = False


settings = Settings()
# print(str(settings.db.db_url))
