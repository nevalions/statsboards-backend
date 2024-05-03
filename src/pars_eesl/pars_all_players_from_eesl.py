import asyncio
import os
from pathlib import Path
from pprint import pprint
from urllib.parse import urlparse

import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

from src.core.config import uploads_path
from src.helpers import get_url
from src.helpers.file_service import file_service
from src.helpers.text_helpers import ru_to_eng_datetime_month

from src.pars_eesl.pars_settings import BASE_ALL_PLAYERS_URL, BASE_PLAYER


async def collect_players_dob_from_all_eesl(player_eesl_id: int, base_url: str = BASE_PLAYER):
    url = base_url + str(player_eesl_id)
    print(url)
    try:
        req = get_url(url)
        soup = BeautifulSoup(req.content, "lxml")
        dob_text = soup.find("span", class_="player-promo__value").text.strip().lower()
        dob_text_eng = ru_to_eng_datetime_month(dob_text)
        return datetime.strptime(dob_text_eng, "%d %B %Y")
        # return datetime.strptime(dob_text_eng, "%Y-%m-%d")
    except requests.exceptions.Timeout:
        print("Timeout occurred")


async def parse_all_players_from_eesl_and_create_jsons():
    try:
        players = await parse_all_players_from_eesl_index_page_eesl()
        print(len(players))
        return players
    except Exception as ex:
        print(ex)
        print(f"Something goes wrong, maybe no data")


async def parse_all_players_from_eesl_index_page_eesl(base_url: str = BASE_ALL_PLAYERS_URL, limit: int | None = None):
    players_in_eesl = []
    num = 0

    while True:
        remaining_limit = limit - len(players_in_eesl) if limit is not None else None

        print(f"Parsing page: {num}")
        url = base_url if num == 0 else f"{base_url}?page={num + 1}"
        req = get_url(url)
        soup = BeautifulSoup(req.content, "lxml")
        all_eesl_players = soup.find_all("tr", class_="table__row")

        if not all_eesl_players:
            print('No players found on the page, stopping.')
            break

        await get_player_from_eesl_participants(players_in_eesl, all_eesl_players, remaining_limit)

        if limit is not None and len(players_in_eesl) >= limit:
            print(f'Reached the limit of {limit} players, stopping.')
            break

        # Check if it's the last page after getting players from the page
        # pagination_buttons = soup.find_all(
        #     "li",
        #     class_="pagination-section__item pagination-section__item--arrow"
        # )
        #
        # # If there's a disabled class present in any of the pagination buttons, we stop.
        # if any('disabled' in button.get('class', []) for button in pagination_buttons):
        #     print('Reached the last page.')
        #     break

        # next_page_disabled = soup.find(
        #     "li",
        #     class_="pagination-section__item--arrow pagination-section__item--disabled"
        # )
        #
        # if next_page_disabled:
        #     print('Reached the last page.')
        #     break

        # Pagination logic
        pagination = soup.find("ul", {"id": "players-pagination"})
        if pagination:
            # Find the 'next' button. It's typically the last 'li' in the pagination 'ul'.
            next_button = pagination.find_all("li", class_="pagination-section__item--arrow")[-1]
            # Check if the 'next' button is disabled
            is_disabled = "pagination-section__item--disabled" in next_button["class"]
            if is_disabled:
                print('Reached the last page, stopping.')
                break

        # If a limit is set and we've reached it, stop the loop
        if limit is not None and len(players_in_eesl) >= limit:
            print(f'Reached the limit of {limit} players, stopping.')
            break
        num += 1

    return players_in_eesl


# async def parse_all_players_from_eesl_index_page_eesl(base_url: str = BASE_ALL_PLAYERS_URL, limit: int | None = None):
#     players_in_eesl = []
#     num = 0
#
#     while True:
#         print(num)
#         if num == 0 and num < 1:
#             url = base_url
#             req = get_url(url)
#             soup = BeautifulSoup(req.content, "lxml")
#             all_eesl_players = soup.find_all("tr", class_="table__row")
#             await get_player_from_eesl_participants(players_in_eesl, all_eesl_players,
#                                                     limit - len(players_in_eesl) if limit is not None else float('inf'))
#
#             if limit is not None and len(players_in_eesl) >= limit:
#                 print(f'Reached the limit of {limit} players, stopping.')
#                 break
#             # await get_player_from_eesl_participants(players_in_eesl, all_eesl_players)
#             num += 1
#         else:
#             url = base_url + f"?page={num + 1}"
#             req = get_url(url)
#             soup = BeautifulSoup(req.content, "lxml")
#             all_eesl_players = soup.find_all("tr", class_="table__row")
#             await get_player_from_eesl_participants(players_in_eesl, all_eesl_players, None)
#
#             stop = soup.find(
#                 "li",
#                 class_="pagination-section__item pagination-section__item--arrow "
#                        "pagination-section__item--disabled",
#             )
#             if stop:
#                 print('PARSING FINISHED')
#                 break
#             num += 1
#
#     return players_in_eesl


# async def get_player_from_eesl_participants(players_in_eesl, all_eesl_players):
async def get_player_from_eesl_participants(players_in_eesl, all_eesl_players, remaining_limit):
    for ppp in all_eesl_players:
        if remaining_limit == 0:
            break
        try:
            if ppp:
                player_eesl_id = int(
                    re.findall(
                        "\d+", ppp.find("a", class_="table__player").get("href")
                    )[0]
                )
                player_full_name = (
                    ppp.find("span", class_="table__player-name").text.strip().lower()
                )
                player_first_name = player_full_name.split(" ")[1]
                player_second_name = player_full_name.split(" ")[0]
                img_url, extension = (
                    ppp.find("img", class_="table__player-img")
                    .get("src")
                    .strip()
                    .split("_")
                )
                player_img_url = f"{img_url}.{extension.split('.')[1]}"

                icon_image_height = 100
                web_view_image_height = 400

                path = urlparse(player_img_url).path
                ext = Path(path).suffix
                person_image_filename = f'{player_eesl_id}_{player_second_name}_{player_first_name}{ext}'
                person_image_filename_resized_icon = f'{player_eesl_id}_{player_second_name}_{player_first_name}_{icon_image_height}px{ext}'
                person_image_filename_resized_web_view = f'{player_eesl_id}_{player_second_name}_{player_first_name}_{web_view_image_height}px{ext}'

                image_path = os.path.join(
                    uploads_path,
                    f"persons/photos/{person_image_filename}"
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
                    person_image_filename_resized_icon,
                )

                # print(image_path)
                # print(relative_image_path)

                # await file_service.download_image(player_img_url, image_path)
                await file_service.download_and_resize_image(
                    player_img_url,
                    image_path,
                    resized_icon_image_path,
                    resized_web_image_path,
                    icon_height=icon_image_height,
                    web_view_height=web_view_image_height,
                )

                player_dob = await collect_players_dob_from_all_eesl(player_eesl_id)
                player_with_person = {
                    'person': {
                        'first_name': player_first_name,
                        'second_name': player_second_name,
                        'person_photo_url': relative_image_path,
                        'person_photo_icon_url': relative_image_icon_path,
                        'person_photo_web_url': relative_image_web_path,
                        'person_dob': player_dob,
                        'person_eesl_id': player_eesl_id,
                    },
                    'player': {
                        'sport_id': '1',
                        'player_eesl_id': player_eesl_id,
                    }
                }
                # player = {
                #     "player_eesl_id": player_eesl_id,
                #     "player_full_name": player_full_name,
                #     "player_first_name": player_first_name,
                #     "player_second_name": player_second_name,
                #     "player_img_url": player_img_url,
                #     "player_dob": player_dob,
                # }

                players_in_eesl.append(player_with_person.copy())
                if remaining_limit is not float('inf'):
                    remaining_limit -= 1
        except Exception as ex:
            print(ex)


async def main():
    # m = await parse_all_players_from_eesl_and_create_jsons()
    m = await parse_all_players_from_eesl_index_page_eesl(limit=2)
    # m = collect_players_dob_from_all_eesl(331)
    pprint(m)


if __name__ == "__main__":
    asyncio.run(main())
