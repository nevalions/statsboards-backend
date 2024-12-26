import logging
import logging.config
import yaml
from pathlib import Path

print(f"Absolute parent path: {Path(__file__).parent.absolute()}")
logs_dir = Path(__file__).parent / "logs"
logs_config_yaml = Path(__file__).parent / "logging-config.yaml"
logs_dir.mkdir(parents=True, exist_ok=True)


def setup_logging(config_path=logs_config_yaml):
    # Resolve the full path of the config file
    print(f"Loading logging configuration from {config_path}")

    # Load YAML configuration
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    # Define the log directory and add it to the configuration
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Replace the placeholder with the actual log directory path
    config["handlers"]["file"]["filename"] = str(logs_dir / "backend.log")

    # Apply the logging configuration
    logging.config.dictConfig(config)

    print(
        f'Logging setup completed. Log file: {config["handlers"]["file"]["filename"]}'
    )
