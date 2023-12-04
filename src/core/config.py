from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
import platform

load_dotenv()
os_sys = platform.system()

BASE_DIR = Path(__file__).parent.parent

host = str(os.getenv("HOST"))
user = str(os.getenv("DB_USER"))
password = str(os.getenv("PASSWORD"))
db_name = str(os.getenv("DB_NAME"))
port = str(os.getenv("PORT"))


class DbSettings(BaseModel):
    url: str = f"postgresql+asyncpg://{user}:{password}@{host}:{str(port)}/{db_name}"
    echo: bool = False
    # echo: bool = True


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"

    db: DbSettings = DbSettings()
    db_echo: bool = True


settings = Settings()
