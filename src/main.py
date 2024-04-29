import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.core.config import uploads_path
from src.core.models.base import ws_manager
from src.playclocks import api_playclock_router
from src.gameclocks import api_gameclock_router

from src.sports import api_sport_router
from src.seasons import api_pars_season_router, api_season_router
from src.tournaments import api_tournament_router, template_tournament_router
from src.teams import api_team_router
from src.team_tournament import api_team_tournament_router
from src.matches import api_match_router, template_match_router
from src.matchdata import api_matchdata_router
from src.scoreboards import api_scoreboards_router
from src.sponsors import api_sponsor_router
from src.sponsor_lines import api_sponsor_line_router
from src.sponsor_sponsor_line_connection import api_sponsor_sponsor_line_router
from src.person import api_person_router
from src.player import api_player_router
from src.player_team_tournament import api_player_team_tournament_router

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

app.include_router(api_pars_season_router)

# Add these event handlers in your startup code
app.add_event_handler("startup", ws_manager.startup)
app.add_event_handler("shutdown", ws_manager.shutdown)

print('FASTAPI STATSBOARD STARTED!')
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [allowed_origins] if allowed_origins == "*" else allowed_origins.split(",")
print(f"allowed_origins: {origins}")

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
