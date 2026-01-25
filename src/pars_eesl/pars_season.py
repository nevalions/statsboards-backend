import logging
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.helpers import get_url
from src.helpers.file_service import file_service
from src.pars_eesl.pars_settings import BASE_SEASON_URL, SEASON_ID

logger = logging.getLogger("backend_logger_parser_eesl")
ITEM_PARSED = "SEASON"
ITEM_GOT = "TOURNAMENT"


async def parse_season_and_create_jsons(
    _id: int, season_id: int | None = None, sport_id: int | None = None
):
    logger.debug(
        f"Starting create parsed json for {ITEM_PARSED} of {ITEM_GOT} id:{_id} season_id:{season_id} sport_id:{sport_id}"
    )
    try:
        # _id = 8  # 2024
        data = await parse_season_index_page_eesl(_id, season_id=season_id, sport_id=sport_id)
        logger.debug(f"Parsed json for {ITEM_PARSED} id{_id} data: {data}")
        return data
    except Exception as ex:
        logger.error(
            f"Something goes wrong with creating parsed json, maybe no data in {ITEM_PARSED} id:{_id}, {ex}",
            exc_info=True,
        )
        return None


async def parse_season_index_page_eesl(
    _id: int,
    base_url: str = BASE_SEASON_URL,
    season_id: int | None = None,
    sport_id: int | None = None,
):
    logger.debug(f"Starting parse for eesl {ITEM_PARSED} id:{_id} url:{base_url}{_id}")
    tournaments_in_season = []

    req = await get_url(base_url + str(_id))
    if req is None:
        logger.warning(f"Failed to fetch season page for id:{_id}")
        return None
    # logger.debug(f"Request: {req}")
    soup = BeautifulSoup(req.content, "lxml")
    # logger.debug(f"Soup: {soup}")

    all_season_tournaments = soup.find_all("li", class_="tournaments-archive__item")
    # logger.debug(f"All {ITEM_PARSED}'s {ITEM_GOT} html: {all_season_tournaments}")
    if all_season_tournaments:
        for t in all_season_tournaments:
            # logger.debug(f"Parsing {ITEM_GOT}: {t}")
            try:
                tournament_title = (
                    t.find("a", class_="tournaments-archive__link").get("title").lower().strip()
                )
                logger.debug(f"{ITEM_GOT} title: {tournament_title}")
                tournament_logo_url = t.find("img", class_="tournaments-archive__img").get("src")
                logger.debug(f"{ITEM_GOT} logo url: {tournament_logo_url}")
                path = urlparse(tournament_logo_url).path
                Path(path).suffix

                icon_image_height = 100
                web_view_image_height = 400

                image_info = await file_service.download_and_process_image(
                    img_url=tournament_logo_url,
                    image_type_prefix="tournaments/logos/",
                    image_title=tournament_title,
                    icon_height=icon_image_height,
                    web_view_height=web_view_image_height,
                )

                try:
                    final_tournament = {
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
                        "season_id": season_id if season_id is not None else SEASON_ID,
                        "sport_id": sport_id if sport_id is not None else 1,
                    }
                    logger.info(f"Final {ITEM_GOT} data: {final_tournament}")
                    tournaments_in_season.append(final_tournament.copy())
                except Exception as ex:
                    logger.error(
                        f"Problem parsing final {ITEM_GOT} data for {ITEM_PARSED} id:{_id}, {ex}",
                        exc_info=True,
                    )
            except Exception as ex:
                logger.error(
                    f"Problem parsing {ITEM_GOT} data for {ITEM_PARSED} id:{_id}, {ex}",
                    exc_info=True,
                )
        logger.info(f"Parsed {ITEM_GOT}s for {ITEM_PARSED} id:{_id}: {tournaments_in_season}")
        return tournaments_in_season
    else:
        logger.warning(f"No {ITEM_GOT}s found for eesl {ITEM_PARSED} id:{_id}")
        return None
