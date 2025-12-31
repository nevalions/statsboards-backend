import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from pydantic import Field, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.exceptions import ConfigurationError
from src.logging_config import get_logger

load_dotenv()
logger = logging.getLogger("backend_logger_config")

SSL_KEY = os.getenv("SSL_KEYFILE")
SSL_CER = os.getenv("SSL_CERTFILE")
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


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_", extra="allow")
    host: str = ""
    user: str = ""
    password: str = ""
    name: str = ""
    port: int = 5432

    @field_validator("host", "user", "password", "name")
    @classmethod
    def validate_not_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ConfigurationError(
                f"Database {info.field_name} cannot be empty",
                {"field": info.field_name},
            )
        return v.strip()

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ConfigurationError(
                f"Database port must be between 1 and 65535, got {v}",
                {"port": v},
            )
        return v

    @property
    def db_url(self) -> str:
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

    def db_url_websocket(self) -> str:
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

    def validate_connection_string(self) -> None:
        try:
            self.db_url
        except Exception as e:
            raise ConfigurationError(
                f"Invalid database connection string: {e}",
                {
                    "host": self.host,
                    "port": self.port,
                    "database": self.name,
                    "user": self.user,
                },
            ) from e


class TestDbSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.test.local", env_prefix="DB_TEST_", extra="allow"
    )
    host: str = ""
    user: str = ""
    password: str = ""
    name: str = ""
    port: int = 5432

    @field_validator("host", "user", "password", "name")
    @classmethod
    def validate_not_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ConfigurationError(
                f"Test database {info.field_name} cannot be empty",
                {"field": info.field_name},
            )
        return v.strip()

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ConfigurationError(
                f"Test database port must be between 1 and 65535, got {v}",
                {"port": v},
            )
        return v

    @property
    def test_db_url(self) -> str:
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

    def test_db_url_websocket(self) -> str:
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

    def validate_connection_string(self) -> None:
        try:
            self.test_db_url
        except Exception as e:
            raise ConfigurationError(
                f"Invalid test database connection string: {e}",
                {
                    "host": self.host,
                    "port": self.port,
                    "database": self.name,
                    "user": self.user,
                },
            ) from e


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")
    # api_v1_prefix: str = "/api/v1"
    db: DbSettings = Field(default_factory=DbSettings)
    test_db: TestDbSettings = Field(default_factory=TestDbSettings)
    db_echo: bool = False
    allowed_origins: str = Field(
        default="*", description="Comma-separated list of allowed CORS origins"
    )
    ssl_keyfile: str | None = Field(
        default=None, description="Path to SSL private key file"
    )
    ssl_certfile: str | None = Field(
        default=None, description="Path to SSL certificate file"
    )
    current_season_id: str | None = Field(
        default=None, description="Current season ID for EESL parsing"
    )
    logs_config: str = Field(
        default="logging-config_info.yaml",
        description="Logging configuration file name",
    )

    @field_validator("allowed_origins")
    @classmethod
    def validate_allowed_origins(cls, v: str) -> str:
        if v == "*":
            return v
        origins = [origin.strip() for origin in v.split(",")]
        for origin in origins:
            if not origin:
                raise ConfigurationError(
                    "Empty origin found in ALLOWED_ORIGINS",
                    {"allowed_origins": v},
                )
            if not origin.startswith(("http://", "https://", "*")):
                raise ConfigurationError(
                    f"Invalid origin format: {origin}. Must start with http://, https://, or *",
                    {"allowed_origins": v},
                )
        return v

    @model_validator(mode="after")
    def validate_ssl_files(self) -> "Settings":
        if bool(self.ssl_keyfile) != bool(self.ssl_certfile):
            raise ConfigurationError(
                "Both SSL_KEYFILE and SSL_CERTFILE must be provided or neither",
                {
                    "ssl_keyfile": self.ssl_keyfile,
                    "ssl_certfile": self.ssl_certfile,
                },
            )
        return self

    def validate_paths_exist(self) -> None:
        """Validate that all required paths exist and are accessible."""
        validation_errors = []

        paths_to_validate = [
            ("static_main_path", static_main_path, "required"),
            ("uploads_path", uploads_path, "required"),
        ]

        optional_paths = [
            ("template_path", template_path),
            ("static_path", static_path),
        ]

        if self.ssl_keyfile and SSL_KEY:
            paths_to_validate.append(("ssl_keyfile", SSL_KEY, "required"))
        if self.ssl_certfile and SSL_CER:
            paths_to_validate.append(("ssl_certfile", SSL_CER, "required"))

        for path_name, path_value, requirement in paths_to_validate:
            if path_value and not Path(path_value).exists():
                if requirement == "required":
                    validation_errors.append(
                        f"Required path '{path_name}' does not exist: {path_value}"
                    )
                else:
                    logger.warning(
                        f"Optional path '{path_name}' does not exist: {path_value}"
                    )
            elif path_value and not os.access(path_value, os.R_OK):
                validation_errors.append(
                    f"Path '{path_name}' is not readable: {path_value}"
                )

        for path_name, path_value in optional_paths:
            if path_value and not Path(path_value).exists():
                logger.warning(
                    f"Optional path '{path_name}' does not exist: {path_value}"
                )
            elif path_value and not os.access(path_value, os.R_OK):
                logger.warning(
                    f"Optional path '{path_name}' is not readable: {path_value}"
                )

        if validation_errors:
            raise ConfigurationError(
                "Path validation failed",
                {"errors": validation_errors},
            )

    def validate_database_settings(self) -> None:
        """Validate database connection strings."""
        if not os.getenv("TESTING"):
            self.db.validate_connection_string()
        self.test_db.validate_connection_string()

    def validate_all(self) -> None:
        """
        Perform all configuration validations.

        This should be called during application startup to ensure
        all configuration is valid before the application starts.
        """
        self.logger = get_logger("backend_logger_config", self)
        self.logger.info("Starting configuration validation")

        try:
            self.validate_paths_exist()
            self.logger.info("Path validation successful")
        except ConfigurationError as e:
            self.logger.error(f"Path validation failed: {e.message}", exc_info=True)
            raise

        try:
            self.validate_database_settings()
            self.logger.info("Database settings validation successful")
        except ConfigurationError as e:
            self.logger.error(
                f"Database settings validation failed: {e.message}", exc_info=True
            )
            raise

        self.logger.info("Configuration validation complete")


settings = Settings()
