import os
import logging
import logging.config
import yaml
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Create log directory and resolve paths
print(f"Absolute parent path: {Path(__file__).parent.absolute()}")
logs_config = os.environ["LOGS_CONFIG"]
print(f"Logs config: {logs_config}")
logs_dir = Path(__file__).parent / "logs"
logs_config_yaml = Path(__file__).parent / logs_config
logs_dir.mkdir(parents=True, exist_ok=True)


class ContextFilter(logging.Filter):
    """Enhanced filter that ensures class name is always available in log records"""

    def filter(self, record):
        # Check if classname is not set and set it to a default value
        if not hasattr(record, "classname"):
            # Try to get class name from the caller if available
            if hasattr(record, "name"):
                parts = record.name.split(".")
                record.classname = parts[-1] if len(parts) > 1 else "None"
            else:
                record.classname = "None"
        return True


class ClassNameAdapter(logging.LoggerAdapter):
    """Adapter that automatically adds class name to log records"""

    def __init__(self, logger: logging.Logger, class_instance: Optional[object] = None):
        extra = {
            "classname": class_instance.__class__.__name__ if class_instance else "None"
        }
        super().__init__(logger, extra)

    def process(self, msg, kwargs):
        # Ensure our extra context is passed through
        kwargs.setdefault("extra", {}).update(self.extra)
        return msg, kwargs


def get_logger(
    name: str, class_instance: Optional[object] = None
) -> logging.LoggerAdapter:
    """
    Get a logger with class name support.

    Args:
        name: Logger name
        class_instance: Optional instance of the class using the logger

    Returns:
        LoggerAdapter with class name support
    """
    logger = logging.getLogger(name)
    return ClassNameAdapter(logger, class_instance)


def setup_logging(config_path=logs_config_yaml):
    """Set up logging with the enhanced configuration"""
    # Load YAML configuration
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    # Define the log directory and add it to the configuration
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Replace the placeholder with the actual log directory path
    config["handlers"]["file"]["filename"] = str(logs_dir / "backend.log")

    # Add context filter configuration
    config.setdefault("filters", {})["context_filter"] = {
        "()": "src.logging_config.ContextFilter"  # Use the full path
    }

    # Apply context filter to all handlers
    for handler in config["handlers"].values():
        if "filters" not in handler:
            handler["filters"] = []
        if "context_filter" not in handler["filters"]:
            handler["filters"].append("context_filter")

    # Apply context filter to all loggers
    for logger in config["loggers"].values():
        if "filters" not in logger:
            logger["filters"] = []
        if "context_filter" not in logger["filters"]:
            logger["filters"].append("context_filter")

    try:
        logging.config.dictConfig(config)
    except Exception as e:
        print(f"Error configuring logging: {e}")
        # Fallback to basic configuration if the custom setup fails
        logging.basicConfig(level=logging.INFO)
