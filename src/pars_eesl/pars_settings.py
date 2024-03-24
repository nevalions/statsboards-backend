import os

BASE_URL = "https://eesl.pro/"
BASE_ALL_PLAYERS_URL = BASE_URL + "participants/players"
BASE_PLAYER = BASE_URL + "player/"
BASE_SEASON_URL = BASE_URL + "tournaments?season_id="
BASE_TOURNAMENT_URL = BASE_URL + "tournament/"
BASE_TEAM_URL = BASE_URL + "team/"  # default
BASE_TEAM_TOURNAMENT_URL = BASE_TOURNAMENT_URL + "teams/application?team_id="  # tourn
BASE_MATCH_URL = BASE_URL + "match/"
SEASON_ID = os.getenv('CURRENT_SEASON_ID')
match_id = "29"
