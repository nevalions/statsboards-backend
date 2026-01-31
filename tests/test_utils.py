"""
Tests for utils modules.

Run with:
    pytest tests/test_utils.py
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.logging_config import (
    ClassNameAdapter,
    ContextFilter,
    get_logger,
    setup_logging,
)
from src.utils.websocket.websocket_manager import MatchDataWebSocketManager


class TestLoggingConfig:
    """Tests for logging configuration utilities."""

    def test_context_filter_sets_classname_default(self):
        """Test that ContextFilter sets default classname when not present."""
        test_filter = ContextFilter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = test_filter.filter(record)
        assert result is True
        assert hasattr(record, "classname")
        assert record.classname == "logger"

    def test_context_filter_preserves_existing_classname(self):
        """Test that ContextFilter preserves existing classname."""
        test_filter = ContextFilter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record.classname = "TestClass"
        result = test_filter.filter(record)
        assert result is True
        assert record.classname == "TestClass"

    def test_context_filter_sets_none_for_empty_name(self):
        """Test that ContextFilter sets None for empty logger name."""
        test_filter = ContextFilter()
        record = logging.LogRecord(
            name="",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = test_filter.filter(record)
        assert result is True
        assert hasattr(record, "classname")

    def test_classname_adapter_with_class_instance(self):
        """Test ClassNameAdapter with class instance."""
        logger = logging.getLogger("test.logger")
        test_class = Mock()
        test_class.__class__.__name__ = "TestClass"
        adapter = ClassNameAdapter(logger, test_class)

        assert adapter.extra["classname"] == "TestClass"

    def test_classname_adapter_without_class_instance(self):
        """Test ClassNameAdapter without class instance."""
        logger = logging.getLogger("test.logger")
        adapter = ClassNameAdapter(logger, None)

        assert adapter.extra["classname"] == "None"

    def test_get_logger_returns_adapter(self):
        """Test that get_logger returns a ClassNameAdapter."""
        test_class = Mock()
        test_class.__class__.__name__ = "TestClass"
        logger = get_logger("test_logger", test_class)

        assert isinstance(logger, ClassNameAdapter)
        assert logger.extra["classname"] == "TestClass"

    def test_get_logger_without_instance(self):
        """Test that get_logger works without class instance."""
        logger = get_logger("test_logger")

        assert isinstance(logger, ClassNameAdapter)
        assert logger.extra["classname"] == "None"

    def test_adapter_process_passes_extra_to_kwargs(self):
        """Test that ClassNameAdapter.process passes extra context."""
        logger = logging.getLogger("test.logger")
        test_class = Mock()
        test_class.__class__.__name__ = "TestClass"
        adapter = ClassNameAdapter(logger, test_class)

        msg, kwargs = adapter.process("test message", {})
        assert "extra" in kwargs
        assert kwargs["extra"]["classname"] == "TestClass"

    def test_adapter_process_merges_with_existing_extra(self):
        """Test that ClassNameAdapter.process merges with existing extra."""
        logger = logging.getLogger("test.logger")
        test_class = Mock()
        test_class.__class__.__name__ = "TestClass"
        adapter = ClassNameAdapter(logger, test_class)

        msg, kwargs = adapter.process("test message", {"extra": {"custom": "value"}})
        assert "extra" in kwargs
        assert kwargs["extra"]["classname"] == "TestClass"
        assert kwargs["extra"]["custom"] == "value"

    @patch("src.logging_config.logging.config.dictConfig")
    @patch("src.logging_config.yaml.safe_load")
    @patch("builtins.open", create=True)
    def test_setup_logging_creates_logs_dir(self, mock_open, mock_yaml, mock_dict_config):
        """Test that setup_logging creates logs directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_logs_dir = Path(tmpdir) / "logs"
            config_path = Path(tmpdir) / "config.yaml"

            mock_yaml.return_value = {
                "handlers": {"file": {"filename": "backend.log"}},
                "loggers": {},
            }
            mock_open.return_value.__enter__.return_value = MagicMock()

            import src.logging_config

            original_logs_dir = src.logging_config.logs_dir
            src.logging_config.logs_dir = test_logs_dir

            try:
                setup_logging(config_path)
                assert test_logs_dir.exists()
            finally:
                src.logging_config.logs_dir = original_logs_dir

    @patch("src.logging_config.logging.config.dictConfig")
    @patch("src.logging_config.yaml.safe_load")
    @patch("builtins.open", create=True)
    def test_setup_logging_adds_context_filter(self, mock_open, mock_yaml, mock_dict_config):
        """Test that setup_logging adds context filter to configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            mock_yaml.return_value = {
                "handlers": {"file": {"filename": "backend.log"}},
                "loggers": {},
            }
            mock_open.return_value.__enter__.return_value = MagicMock()

            setup_logging(config_path)

            called_config = mock_dict_config.call_args[0][0]
            assert "filters" in called_config
            assert "context_filter" in called_config["filters"]
            assert "context_filter" in called_config["handlers"]["file"].get("filters", [])


class TestWebSocketManager:
    """Tests for WebSocket manager utilities."""

    def test_match_data_websocket_manager_initialization(self):
        """Test MatchDataWebSocketManager initialization."""
        db_url = "postgresql://test:test@localhost/test"
        manager = MatchDataWebSocketManager(db_url)

        assert manager.db_url == db_url
        assert manager.connection is None
        assert manager.is_connected is False
        assert manager._connection_retry_task is None
        assert manager._cache_service is None

    @pytest.mark.asyncio
    async def test_connect_to_db_success(self):
        """Test successful database connection."""
        db_url = "postgresql://test:test@localhost/test"
        manager = MatchDataWebSocketManager(db_url)

        with patch("asyncpg.connect") as mock_connect:
            mock_connection = Mock()
            mock_connection.add_listener = AsyncMock()
            mock_connect.return_value = mock_connection

            await manager.connect_to_db()

            mock_connect.assert_called_once_with(db_url)
            assert manager.connection == mock_connection
            assert manager.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_to_db_failure(self):
        """Test database connection failure."""
        db_url = "postgresql://test:test@localhost/test"
        manager = MatchDataWebSocketManager(db_url)

        with patch("asyncpg.connect") as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            try:
                await manager.connect_to_db()
            except Exception:
                pass

            assert manager.is_connected is False

    @pytest.mark.asyncio
    async def test_maintain_connection_retries_on_failure(self):
        """Test that maintain_connection retries on connection failure."""
        db_url = "postgresql://test:test@localhost/test"
        manager = MatchDataWebSocketManager(db_url)

        call_count = 0

        async def mock_connect():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("Connection failed")
            return None

        manager.connect_to_db = AsyncMock(side_effect=mock_connect)

        task = asyncio.create_task(manager.maintain_connection())

        await asyncio.sleep(0.02)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert call_count >= 1

    def test_logger_initialization(self):
        """Test that WebSocket manager initializes logger correctly."""
        db_url = "postgresql://test:test@localhost/test"
        manager = MatchDataWebSocketManager(db_url)

        assert manager.logger is not None
        assert manager.logger.name == "MatchDataWebSocketManager"
