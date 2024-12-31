import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import re

from src.core.config import uploads_path
from src.helpers import get_url
from src.helpers.file_service import file_service
from src.logging_config import setup_logging
from src.pars_eesl.pars_settings import BASE_SEASON_URL, SEASON_ID

setup_logging()
logger = logging.getLogger("backend_logger_parser_eesl")


def parse_season_and_create_jsons(s_id: int):
    logger.debug(f"Starting create parsed json for season id:{s_id}")
    try:
        # s_id = 8  # 2024
        data = parse_season_index_page_eesl(s_id)
        logger.debug(f"Parsed json for season id{s_id} data: {data}")
        return data
    except Exception as ex:
        logger.error(
            f"Something goes wrong with creating parsed json, maybe no data in season id:{s_id}, {ex}",
            exc_info=True,
        )
        return None


async def parse_season_index_page_eesl(s_id: int, base_url: str = BASE_SEASON_URL):
    logger.debug(f"Starting parse for eesl season id:{s_id} url:{base_url}{s_id}")
    tournaments_in_season = []

    req = get_url(base_url + str(s_id))
    logger.debug(f"Request: {req}")
    soup = BeautifulSoup(req.content, "lxml")
    logger.debug(f"Soup: {soup}")

    all_season_tournaments = soup.find_all("li", class_="tournaments-archive__item")
    logger.debug(f"All season tournaments html: {all_season_tournaments}")
    if all_season_tournaments:
        for t in all_season_tournaments:
            logger.debug(f"Parsing tournament: {t}")
            try:
                tournament_title = (
                    t.find("a", class_="tournaments-archive__link")
                    .get("title")
                    .lower()
                    .strip()
                )
                logger.debug(f"Tournament title: {tournament_title}")
                tournament_logo_url = t.find(
                    "img", class_="tournaments-archive__img"
                ).get("src")
                logger.debug(f"Tournament logo url: {tournament_logo_url}")
                path = urlparse(tournament_logo_url).path
                ext = Path(path).suffix

                icon_image_height = 100
                web_view_image_height = 400

                image_info = await file_service.download_and_process_image(
                    img_url=tournament_logo_url,
                    image_type_prefix="tournaments/logos/",
                    image_title=tournament_title,
                    icon_height=icon_image_height,
                    web_view_height=web_view_image_height,
                )

                tourn = {
                    "tournament_eesl_id": int(
                        re.findall(
                            r"\d+",
                            t.find("a", class_="tournaments-archive__link").get("href"),
                        )[0]
                    ),
                    "title": tournament_title,
                    "description": "",
                    "tournament_logo_url": image_info["image_url"],
                    "tournament_logo_icon_url": image_info["image_icon_url"],
                    "tournament_logo_web_url": image_info["image_webview_url"],
                    # "season_id": 2,
                    "season_id": SEASON_ID,
                    "sport_id": 1,
                }
                tournaments_in_season.append(tourn.copy())

            except Exception as ex:
                print(ex)
        return tournaments_in_season
    else:
        logger.warning(f"No tournaments found for eesl season id:{s_id}")
        return None


if __name__ == "__main__":
    m = parse_season_and_create_jsons(8)
    print(m)
