import os
from pathlib import Path

import logging
import logging.config
import yaml

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.core.config import uploads_path
from src.core.models.base import ws_manager
from src.football_events import api_football_event_router
from src.gameclocks import api_gameclock_router
from src.matchdata import api_matchdata_router
from src.matches import api_match_router, template_match_router
from src.person import api_person_router
from src.playclocks import api_playclock_router
from src.player import api_player_router
from src.player_match import api_player_match_router
from src.player_team_tournament import api_player_team_tournament_router
from src.positions import api_position_router
from src.scoreboards import api_scoreboards_router
from src.seasons import api_pars_season_router, api_season_router
from src.sponsor_lines import api_sponsor_line_router
from src.sponsor_sponsor_line_connection import api_sponsor_sponsor_line_router
from src.sponsors import api_sponsor_router
from src.sports import api_sport_router
from src.team_tournament import api_team_tournament_router
from src.teams import api_team_router
from src.tournaments import api_tournament_router, template_tournament_router

logger = logging.getLogger("backend_logger_fastapi")

print(f'Absolute parent path: {Path(__file__).parent.absolute()}')
logs_dir = Path(__file__).parent / "logs"
logs_config_yaml = Path(__file__).parent / "logging-config.yaml"
logs_dir.mkdir(parents=True, exist_ok=True)

def setup_logging(config_path=logs_config_yaml):
    # Resolve the full path of the config file
    print(f'Loading logging configuration from {config_path}')

    # Load YAML configuration
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    # Define the log directory and add it to the configuration
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Replace the placeholder with the actual log directory path
    config['handlers']['file']['filename'] = str(logs_dir / "backend.log")

    # Apply the logging configuration
    logging.config.dictConfig(config)

    print(f'Logging setup completed. Log file: {config["handlers"]["file"]["filename"]}')


setup_logging()

# Check if the log file is writable
log_file_path = logs_dir / "backend.log"

if os.access(log_file_path, os.W_OK):
    logger.debug("Log file is writable.")
else:
    logger.error("Log file is not writable.")
app = FastAPI()

app.include_router(api_sport_router)
app.include_router(api_season_router)
app.include_router(api_tournament_router)
app.include_router(template_tournament_router)
app.include_router(api_team_router)
app.include_router(api_team_tournament_router)
app.include_router(api_match_router)
app.include_router(template_match_router)
app.include_router(api_matchdata_router)
app.include_router(api_playclock_router)
app.include_router(api_gameclock_router)
app.include_router(api_scoreboards_router)
app.include_router(api_sponsor_router)
app.include_router(api_sponsor_line_router)
app.include_router(api_sponsor_sponsor_line_router)
app.include_router(api_person_router)
app.include_router(api_player_router)
app.include_router(api_player_team_tournament_router)
app.include_router(api_position_router)
app.include_router(api_player_match_router)
app.include_router(api_football_event_router)

app.include_router(api_pars_season_router)

# Add these event handlers in your startup code
app.add_event_handler("startup", ws_manager.startup)
app.add_event_handler("shutdown", ws_manager.shutdown)

logger.info("FastAPI app initialized.")
# print("FASTAPI STATSBOARD STARTED!")
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [allowed_origins] if allowed_origins == "*" else allowed_origins.split(",")
# print(f"allowed_origins: {origins}")
logger.info(f"allowed_origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static/uploads",
    StaticFiles(directory=uploads_path),
    name="uploads",
)
