import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.config import DbSettings, Settings
from src.core.config import TestDbSettings as ConfigTestDbSettings
from src.core.exceptions import ConfigurationError


class TestDbSettingsValidation:
    """Test database settings validation."""

    def test_db_url_construction(self):
        """Test that database URL is constructed correctly."""
        db_settings = DbSettings(
            host="localhost",
            user="testuser",
            password="testpass",
            name="testdb",
            port=5432,
        )
        expected_url = "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb"
        assert db_settings.db_url == expected_url

    def test_db_url_websocket_construction(self):
        """Test that WebSocket URL is constructed correctly."""
        db_settings = DbSettings(
            host="localhost",
            user="testuser",
            password="testpass",
            name="testdb",
            port=5432,
        )
        expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
        assert db_settings.db_url_websocket() == expected_url

    def test_validate_not_empty_host(self):
        """Test that empty host raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            DbSettings(host="", user="user", password="pass", name="db")
        assert "host" in str(exc_info.value).lower()

    def test_validate_not_empty_user(self):
        """Test that empty user raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            DbSettings(host="localhost", user="", password="pass", name="db")
        assert "user" in str(exc_info.value).lower()

    def test_validate_not_empty_password(self):
        """Test that empty password raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            DbSettings(host="localhost", user="user", password="", name="db")
        assert "password" in str(exc_info.value).lower()

    def test_validate_not_empty_name(self):
        """Test that empty database name raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            DbSettings(host="localhost", user="user", password="pass", name="")
        assert "name" in str(exc_info.value).lower()

    def test_validate_port_valid(self):
        """Test that valid port is accepted."""
        db_settings = DbSettings(
            host="localhost", user="user", password="pass", name="db", port=5432
        )
        assert db_settings.port == 5432

    def test_validate_port_too_low(self):
        """Test that port below 1 raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            DbSettings(
                host="localhost", user="user", password="pass", name="db", port=0
            )
        assert "port" in str(exc_info.value).lower()

    def test_validate_port_too_high(self):
        """Test that port above 65535 raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            DbSettings(
                host="localhost", user="user", password="pass", name="db", port=70000
            )
        assert "port" in str(exc_info.value).lower()

    def test_whitespace_trimming(self):
        """Test that whitespace is trimmed from field values."""
        db_settings = DbSettings(
            host=" localhost ", user=" user ", password=" pass ", name=" db "
        )
        assert db_settings.host == "localhost"
        assert db_settings.user == "user"
        assert db_settings.password == "pass"
        assert db_settings.name == "db"


class TestTestDbSettingsValidation:
    """Test test database settings validation."""

    def test_test_db_url_construction(self):
        """Test that test database URL is constructed correctly."""
        db_settings = ConfigTestDbSettings(
            host="localhost",
            user="testuser",
            password="testpass",
            name="testdb",
            port=5432,
        )
        expected_url = "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb"
        assert db_settings.test_db_url == expected_url

    def test_test_db_url_websocket_construction(self):
        """Test that test database WebSocket URL is constructed correctly."""
        db_settings = ConfigTestDbSettings(
            host="localhost",
            user="testuser",
            password="testpass",
            name="testdb",
            port=5432,
        )
        expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
        assert db_settings.test_db_url_websocket() == expected_url


class TestSettingsValidation:
    """Test application settings validation."""

    def test_default_allowed_origins(self):
        """Test that default allowed origins is '*"""
        settings = Settings()
        assert settings.allowed_origins == "*"

    def test_validate_allowed_origins_star(self):
        """Test that '*' is accepted as allowed origins."""
        settings = Settings(allowed_origins="*")
        assert settings.allowed_origins == "*"

    def test_validate_allowed_origins_multiple(self):
        """Test that multiple origins are validated correctly."""
        settings = Settings(allowed_origins="http://localhost:3000,https://example.com")
        assert settings.allowed_origins == "http://localhost:3000,https://example.com"

    def test_validate_allowed_origins_invalid_scheme(self):
        """Test that invalid origin scheme raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Settings(allowed_origins="ftp://example.com")
        assert "invalid origin format" in str(exc_info.value).lower()

    def test_validate_allowed_origins_empty_origin(self):
        """Test that empty origin in list raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Settings(allowed_origins="http://localhost:3000,")
        assert "empty origin" in str(exc_info.value).lower()

    def test_validate_ssl_files_both_provided(self):
        """Test that both SSL files can be provided."""
        settings = Settings(
            ssl_keyfile="/path/to/key.pem", ssl_certfile="/path/to/cert.pem"
        )
        assert settings.ssl_keyfile == "/path/to/key.pem"
        assert settings.ssl_certfile == "/path/to/cert.pem"

    def test_validate_ssl_files_none_provided(self):
        """Test that neither SSL file is required."""
        settings = Settings()
        assert settings.ssl_keyfile is None
        assert settings.ssl_certfile is None

    def test_validate_ssl_files_only_key(self):
        """Test that providing only SSL key raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Settings(ssl_keyfile="/path/to/key.pem")
        assert "ssl" in str(exc_info.value).lower()

    def test_validate_ssl_files_only_cert(self):
        """Test that providing only SSL cert raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Settings(ssl_certfile="/path/to/cert.pem")
        assert "ssl" in str(exc_info.value).lower()

    def test_validate_paths_exist_required(self):
        """Test that required paths are validated."""
        settings = Settings()
        static_main_path = Path(__file__).parent.parent / "static"
        if static_main_path.exists():
            settings.validate_paths_exist()

    def test_validate_paths_exist_missing_required(self):
        """Test that missing required path raises ConfigurationError."""
        settings = Settings()
        with patch("src.core.config.static_main_path", "/nonexistent/path"):
            with pytest.raises(ConfigurationError) as exc_info:
                settings.validate_paths_exist()
            assert "path validation failed" in str(exc_info.value).lower()

    def test_validate_database_settings(self):
        """Test that database settings validation works."""
        settings = Settings(
            db=DbSettings(
                host="localhost", user="user", password="pass", name="db", port=5432
            ),
            test_db=ConfigTestDbSettings(
                host="localhost", user="user", password="pass", name="testdb", port=5432
            ),
        )
        settings.validate_database_settings()

    def test_validate_all_skips_main_db_when_testing(self):
        """Test that main database validation is skipped when TESTING environment variable is set."""
        with patch.dict(os.environ, {"TESTING": "1"}):
            settings = Settings()
            settings.validate_all()

    def test_validate_all(self):
        """Test that full validation works when paths exist."""
        settings = Settings()
        static_main_path = Path(__file__).parent.parent / "static"
        if static_main_path.exists():
            settings.validate_all()
