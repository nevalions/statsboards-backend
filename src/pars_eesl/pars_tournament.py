import os
from pathlib import Path
from pprint import pprint
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import re

from src.core.config import uploads_path
from src.helpers import get_url
from src.helpers.file_service import file_service
from src.pars_eesl.pars_settings import BASE_TOURNAMENT_URL


def parse_tournament_matches_and_create_jsons(t_id: int):
    try:
        matches = parse_tournament_matches_index_page_eesl(t_id)
        return matches
    except Exception as ex:
        print(ex)
        print(f"Something goes wrong, maybe no data in tournament id({t_id})")


def parse_tournament_teams_and_create_jsons(t_id: int):
    try:
        teams = parse_tournament_teams_index_page_eesl(t_id)
        return teams
    except Exception as ex:
        print(ex)
        print(f"Something goes wrong, maybe no data in tournament id({t_id})")


async def parse_tournament_teams_index_page_eesl(
        t_id: int, base_url: str = BASE_TOURNAMENT_URL
):
    teams_in_tournament = []
    url = f"{base_url}{str(t_id)}/teams"
    req = get_url(url)
    soup = BeautifulSoup(req.content, "lxml")

    all_tournament_teams = soup.find_all("li", class_="teams__item")

    for t in all_tournament_teams:
        try:
            team_eesl_id = int(
                re.findall(
                    "team_id=(\d+)", t.find("a", class_="teams__logo").get("href")
                )[0])
            team_title = t.find("a", class_="teams__name-link").text.strip().lower()
            team_logo_url = t.find(
                "img", alt=t.find("a", class_="teams__name-link").text.strip()
            ).get("src")
            path = urlparse(team_logo_url).path
            ext = Path(path).suffix

            image_path = os.path.join(uploads_path, f"logos/{team_title}{ext}")
            relative_image_path = os.path.join("/static/uploads/logos", f"{team_title}{ext}")
            print(image_path)

            await file_service.download_image(team_logo_url, image_path)

            team = {
                "team_eesl_id": team_eesl_id,
                "title": team_title,
                "description": "",
                "team_logo_url": relative_image_path,
                "city": '',
                "team_color": '#c01c28',
                "sport_id": 1,
            }
            teams_in_tournament.append(team.copy())
        except Exception as ex:
            print(ex)
    return teams_in_tournament


def parse_tournament_matches_index_page_eesl(
        t_id: int, base_url: str = BASE_TOURNAMENT_URL
):
    matches_in_tournament = []
    url = f"{base_url}{str(t_id)}/calendar"
    req = get_url(url)
    soup = BeautifulSoup(req.content, "lxml")
    all_tournament_matches = soup.select(".schedule__matches-item")

    for mp in all_tournament_matches:
        try:
            match = {
                "match_eesl_id": int(
                    re.findall(
                        "\d+", mp.find("a", class_="schedule__score").get("href")
                    )[0]
                ),
                "eesl_id_team_a": int(
                    mp.find("a", class_="schedule__team-1")
                    .get("href")
                    .strip()
                    .split("=")[1]
                ),
                "eesl_id_team_b": int(
                    mp.find("a", class_="schedule__team-2")
                    .get("href")
                    .strip()
                    .split("=")[1]
                ),
                "tournament_eesl_id": t_id,
            }
            matches_in_tournament.append(match.copy())
        except Exception as ex:
            print(ex)
    return matches_in_tournament


if __name__ == "__main__":
    m = parse_tournament_teams_and_create_jsons(19)
    # m = parse_tournament_matches_and_create_jsons(19)
    pprint(m)
