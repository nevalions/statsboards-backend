import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TypedDict
from urllib.parse import urlparse

from aiohttp import ClientError
from bs4 import BeautifulSoup
from fastapi import HTTPException

from src.core.config import uploads_path
from src.helpers import get_url
from src.helpers.file_service import file_service
from src.helpers.text_helpers import ru_to_eng_datetime_month, convert_cyrillic_filename
from src.logging_config import setup_logging
from src.pars_eesl.pars_settings import BASE_ALL_PLAYERS_URL, BASE_PLAYER

setup_logging()
logger = logging.getLogger("backend_logger_parse_players_from_eesl")
ITEM_GOT = "PLAYER"


class ParsedPlayerData(TypedDict):
    sport_id: str
    player_eesl_id: int


class ParsedPersonData(TypedDict):
    first_name: str
    second_name: str
    person_photo_url: str
    person_photo_icon_url: str
    person_photo_web_url: str
    person_dob: datetime
    person_eesl_id: int


class ParsePlayerWithPersonData(TypedDict):
    person: ParsedPersonData
    player: ParsedPlayerData


async def collect_players_dob_from_all_eesl(
    player_eesl_id: int, base_url: str = BASE_PLAYER
):
    logger.debug("Collect players date of birthday from eesl")
    url = base_url + str(player_eesl_id)
    logger.debug(f"URL: {url}")
    try:
        req = await get_url(url)
        soup = BeautifulSoup(req.content, "lxml")
        dob_text = soup.find("span", class_="player-promo__value").text.strip().lower()
        dob_text_eng = ru_to_eng_datetime_month(dob_text)
        return datetime.strptime(dob_text_eng, "%d %B %Y")
    except asyncio.TimeoutError:
        logger.error("Timeout occur while parsing date of birthday form eesl")
    except Exception as ex:
        logger.error(
            f"Error while parsing date of birthday from eesl: {ex}", exc_info=True
        )


async def collect_player_full_data_eesl(
    player_eesl_id: int, base_url: str = BASE_PLAYER, force_redownload: bool = False
) -> Optional[ParsePlayerWithPersonData]:
    logger.debug(
        f"Collect players full data from eesl (force_redownload={force_redownload})"
    )
    url = base_url + str(player_eesl_id)
    logger.debug(f"URL: {url}")
    try:
        req = await get_url(url)
        soup = BeautifulSoup(req.content, "lxml")
        dob_text = soup.find("span", class_="player-promo__value").text.strip().lower()

        dob_text_eng = ru_to_eng_datetime_month(dob_text)
        dob = datetime.strptime(dob_text_eng, "%d %B %Y")
        logger.debug(f"Parsing DoB {dob}")

        player_full_name = (
            soup.find("p", class_="player-promo__name").text.strip().lower()
        )
        logger.debug(f"Parsing full name {player_full_name}")

        player_first_name = player_full_name.split(" ")[1]
        player_second_name = player_full_name.split(" ")[0]
        logger.debug(
            f"Getting first and second name {player_first_name} {player_second_name}"
        )

        img_url, extension = (
            soup.find("img", class_="player-promo__img").get("src").strip().split("_")
        )
        player_img_url = f"{img_url}.{extension.split('.')[1]}"
        logger.debug(f"Parsing img url {player_img_url}")

        icon_image_height = 100
        web_view_image_height = 400

        logger.debug("Getting image data for persons")
        path = urlparse(player_img_url).path
        ext = Path(path).suffix
        person_image_filename = (
            f"{player_eesl_id}_{player_second_name}_{player_first_name}{ext}"
        )
        person_image_filename = convert_cyrillic_filename(person_image_filename)
        person_image_filename_resized_icon = f"{player_eesl_id}_{player_second_name}_{player_first_name}_{icon_image_height}px{ext}"
        person_image_filename_resized_icon = convert_cyrillic_filename(
            person_image_filename_resized_icon
        )
        person_image_filename_resized_web_view = f"{player_eesl_id}_{player_second_name}_{player_first_name}_{web_view_image_height}px{ext}"
        person_image_filename_resized_web_view = convert_cyrillic_filename(
            person_image_filename_resized_web_view
        )

        image_path = os.path.join(uploads_path, "persons/photos/")
        image_path_with_filename = os.path.join(
            uploads_path, f"persons/photos/{person_image_filename}"
        )

        resized_icon_image_path = os.path.join(
            uploads_path,
            f"persons/photos/{person_image_filename_resized_icon}",
        )
        resized_web_image_path = os.path.join(
            uploads_path,
            f"persons/photos/{person_image_filename_resized_web_view}",
        )

        relative_image_icon_path = os.path.join(
            "/static/uploads/persons/photos",
            person_image_filename_resized_icon,
        )

        relative_image_web_path = os.path.join(
            "/static/uploads/persons/photos",
            person_image_filename_resized_web_view,
        )

        relative_image_path = os.path.join(
            "/static/uploads/persons/photos",
            person_image_filename,
        )

        try:
            logger.debug("Downloading person image")
            await file_service.download_and_resize_image(
                img_url=player_img_url,
                original_file_path=image_path,
                original_image_path_with_filename=image_path_with_filename,
                icon_image_path=resized_icon_image_path,
                web_view_image_path=resized_web_image_path,
                icon_height=icon_image_height,
                web_view_height=web_view_image_height,
            )
        except Exception as ex:
            logger.error(f"Error while downloading person image: {ex}", exc_info=True)

        player_with_person: ParsePlayerWithPersonData = {
            "person": {
                "first_name": player_first_name,
                "second_name": player_second_name,
                "person_photo_url": relative_image_path,
                "person_photo_icon_url": relative_image_icon_path,
                "person_photo_web_url": relative_image_web_path,
                "person_dob": dob,
                "person_eesl_id": player_eesl_id,
            },
            "player": {
                "sport_id": "1",
                "player_eesl_id": player_eesl_id,
            },
        }
        if player_with_person:
            logger.info(f"Final player with person data parsed {player_with_person}")
            return player_with_person
        else:
            raise HTTPException(
                status_code=404,
                detail="Parsed player does not exist",
            )
    except asyncio.TimeoutError:
        logger.error("Timeout occur while parsing player with person from eesl")
    except Exception as ex:
        logger.error(
            f"Error while parsing player with person from eesl: {ex}", exc_info=True
        )


async def parse_all_players_from_eesl_and_create_jsons():
    try:
        logger.debug("Parsing and creat json for all players from eesl")
        players = await parse_all_players_from_eesl_index_page_eesl()
        logger.debug(f"Number of players parsed: {len(players)}")
        return players
    except Exception as ex:
        logger.error(
            f"Error while parsing and creat json for all players from eesl: {ex}",
            exc_info=True,
        )


async def parse_all_players_from_eesl_index_page_eesl(
    base_url: str = BASE_ALL_PLAYERS_URL,
    start_page: int = 0,
    limit: int | None = None,
    season_id: int | None = None,
):
    logger.debug(
        f"Parsing all players from eesl start page {start_page} and limit players {limit}"
    )
    players_in_eesl = []
    num = 0

    if start_page and start_page > 0:
        num = num + start_page - 1
    # players?season_id=8&page=2
    while True:
        remaining_limit = limit - len(players_in_eesl) if limit is not None else None
        logger.debug(f"Parsing page: {num} Remaining limit of players to parse:{limit}")
        url = (
            f"{base_url}?season_id={season_id}"
            if num == 0
            else f"{base_url}?season_id={season_id}&page={num + 1}"
        )
        logger.debug(f"URL:{url}")
        req = await get_url(url)
        soup = BeautifulSoup(req.content, "lxml")
        all_eesl_players = soup.find_all("tr", class_="table__row")

        if not all_eesl_players:
            logger.warning("No players found in eesl, stopping..")
            break

        logger.debug("Parsing all players from eesl")

        try:
            await get_player_from_eesl_participants(
                players_in_eesl, all_eesl_players, remaining_limit
            )
        except Exception as ex:
            logger.error(
                f"Error while getting player from eesl participiants: {ex}",
                exc_info=True,
            )
            break

        if limit is not None and len(players_in_eesl) >= limit:
            logger.warning(f"Reached the limit of {limit} players, stopping...")
            break

        # Pagination logic
        pagination = soup.find("ul", {"id": "players-pagination"})
        if pagination:
            logger.debug("Pagination logic")
            # Find the 'next' button. It's typically the last 'li' in the pagination 'ul'.
            next_button = pagination.find_all(
                "li", class_="pagination-section__item--arrow"
            )[-1]
            # Check if the 'next' button is disabled
            is_disabled = "pagination-section__item--disabled" in next_button["class"]
            if is_disabled:
                logger.warning("Reached the last page, stopping...")
                break

        if limit is not None and len(players_in_eesl) >= limit:
            logger.warning(f"Reached the limit of {limit} players, stopping.")
            break
        num += 1

    return players_in_eesl


async def get_player_from_eesl_participants(
    players_in_eesl, all_eesl_players, remaining_limit
) -> Optional[List[ParsePlayerWithPersonData]] | bool:
    logger.debug("Parsing player from eesl participants")
    has_error = False
    for ppp in all_eesl_players:
        if remaining_limit == 0:
            logger.debug("Remaining limit of players reached. Stopping...")
            break
        try:
            if ppp:
                logger.debug("Parsing player from eesl")
                player_eesl_id = int(
                    re.findall(
                        r"\d+", ppp.find("a", class_="table__player").get("href")
                    )[0]
                )
                logger.debug(f"Parsing player eesl_id: {player_eesl_id}")
                player_full_name = (
                    ppp.find("span", class_="table__player-name").text.strip().lower()
                )
                logger.debug(f"Parsing player full name: {player_full_name}")
                player_first_name = player_full_name.split(" ")[1]
                player_second_name = player_full_name.split(" ")[0]
                logger.debug(
                    f"Parsing player first name and second name: {player_first_name} {player_second_name}"
                )
                img_url, extension = (
                    ppp.find("img", class_="table__player-img")
                    .get("src")
                    .strip()
                    .split("_")
                )
                logger.debug(
                    f"Parsing player image url: {img_url} and extension: {extension}"
                )
                player_img_url = f"{img_url}.{extension.split('.')[1]}"

                icon_image_height = 100
                web_view_image_height = 400

                logger.debug("Getting image data for persons")
                path = urlparse(player_img_url).path
                ext = Path(path).suffix
                person_image_filename = (
                    f"{player_eesl_id}_{player_second_name}_{player_first_name}{ext}"
                )
                person_image_filename = convert_cyrillic_filename(person_image_filename)
                person_image_filename_resized_icon = f"{player_eesl_id}_{player_second_name}_{player_first_name}_{icon_image_height}px{ext}"
                person_image_filename_resized_icon = convert_cyrillic_filename(
                    person_image_filename_resized_icon
                )
                person_image_filename_resized_web_view = f"{player_eesl_id}_{player_second_name}_{player_first_name}_{web_view_image_height}px{ext}"
                person_image_filename_resized_web_view = convert_cyrillic_filename(
                    person_image_filename_resized_web_view
                )

                image_path = os.path.join(uploads_path, "persons/photos/")
                image_path_with_filename = os.path.join(
                    uploads_path, f"persons/photos/{person_image_filename}"
                )

                resized_icon_image_path = os.path.join(
                    uploads_path,
                    f"persons/photos/{person_image_filename_resized_icon}",
                )
                resized_web_image_path = os.path.join(
                    uploads_path,
                    f"persons/photos/{person_image_filename_resized_web_view}",
                )

                relative_image_icon_path = os.path.join(
                    "/static/uploads/persons/photos",
                    person_image_filename_resized_icon,
                )

                relative_image_web_path = os.path.join(
                    "/static/uploads/persons/photos",
                    person_image_filename_resized_web_view,
                )

                relative_image_path = os.path.join(
                    "/static/uploads/persons/photos",
                    person_image_filename,
                )

                try:
                    logger.debug("Downloading person image")
                    await file_service.download_and_resize_image(
                        img_url=player_img_url,
                        original_file_path=image_path,
                        original_image_path_with_filename=image_path_with_filename,
                        icon_image_path=resized_icon_image_path,
                        web_view_image_path=resized_web_image_path,
                        icon_height=icon_image_height,
                        web_view_height=web_view_image_height,
                    )
                except Exception as ex:
                    logger.error(
                        f"Error while downloading person image: {ex}, skipping player {player_eesl_id}",
                        exc_info=True,
                    )
                    has_error = True
                    continue

                player_dob = await collect_players_dob_from_all_eesl(player_eesl_id)
                if player_dob is None:
                    logger.warning(
                        f"Skipping player {player_eesl_id} due to missing DOB"
                    )
                    continue
                player_with_person: ParsePlayerWithPersonData = {
                    "person": {
                        "first_name": player_first_name,
                        "second_name": player_second_name,
                        "person_photo_url": relative_image_path,
                        "person_photo_icon_url": relative_image_icon_path,
                        "person_photo_web_url": relative_image_web_path,
                        "person_dob": player_dob,
                        "person_eesl_id": player_eesl_id,
                    },
                    "player": {
                        "sport_id": "1",
                        "player_eesl_id": player_eesl_id,
                    },
                }
                logger.info(
                    f"Final player with person data parsed {player_with_person}"
                )
                players_in_eesl.append(player_with_person.copy())
                if remaining_limit and remaining_limit is not float("inf"):
                    remaining_limit -= 1
        except asyncio.TimeoutError:
            logger.error("Timeout occur while parsing player with person from eesl")
            return False
        except Exception as ex:
            logger.error(f"Error collecting players from eesl: {ex}", exc_info=True)
            return False if has_error else None


async def main():
    # m = await parse_all_players_from_eesl_and_create_jsons()
    # m = await parse_all_players_from_eesl_index_page_eesl(limit=None)
    # m = collect_players_dob_from_all_eesl(331)
    # pprint(m)
    await collect_player_full_data_eesl(1812)


if __name__ == "__main__":
    asyncio.run(main())
