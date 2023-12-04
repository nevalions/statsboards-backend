from pprint import pprint

import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

from src.helpers import get_url
from src.helpers.text_helpers import ru_to_eng_datetime_month

from src.pars_eesl.pars_settings import BASE_ALL_PLAYERS_URL, BASE_PLAYER


def collect_players_dob_from_all_eesl(player_eesl_id: int, base_url: str = BASE_PLAYER):
    url = base_url + str(player_eesl_id)
    print(url)
    try:
        req = get_url(url)
        soup = BeautifulSoup(req.content, 'lxml')
        dob_text = soup.find('span', class_='player-promo__value').text.strip().lower()
        dob_text_eng = ru_to_eng_datetime_month(dob_text)
        return datetime.strptime(dob_text_eng, '%d %B %Y')
    except requests.exceptions.Timeout:
        print("Timeout occurred")


def parse_all_players_from_eesl_and_create_jsons():
    try:
        players = parse_all_players_from_eesl_index_page_eesl()
        print(len(players))
        return players
    except Exception as ex:
        print(ex)
        print(f'Something goes wrong, maybe no data')


def parse_all_players_from_eesl_index_page_eesl(
        base_url: str = BASE_ALL_PLAYERS_URL):
    players_in_eesl = []
    num = 0

    while True:

        print(num)
        if num == 0:
            url = base_url
            req = get_url(url)
            soup = BeautifulSoup(req.content, 'lxml')
            all_eesl_players = soup.find_all('tr', class_='table__row')
            get_player_from_eesl_participants(players_in_eesl, all_eesl_players)
            num += 1
        else:
            url = base_url + f'?page={num + 1}'
            req = get_url(url)
            soup = BeautifulSoup(req.content, 'lxml')
            all_eesl_players = soup.find_all('tr', class_='table__row')
            get_player_from_eesl_participants(players_in_eesl, all_eesl_players)

            stop = soup.find('li',
                             class_='pagination-section__item pagination-section__item--arrow '
                                    'pagination-section__item--disabled')
            if stop:
                break
            num += 1

    return players_in_eesl


def get_player_from_eesl_participants(players_in_eesl, all_eesl_players):
    for ppp in all_eesl_players:
        try:
            if ppp:
                player_eesl_id = int(re.findall(
                    '\d+',
                    ppp.find('a',
                             class_='table__player').get('href'))[0])
                player_full_name = ppp.find('span',
                                            class_='table__player-name').text.strip().lower()
                player_first_name = player_full_name.split(' ')[1]
                player_second_name = player_full_name.split(' ')[0]
                img_url, extension = ppp.find(
                    'img', class_='table__player-img').get('statsboards-backend').strip().split('_')
                player_img_url = f"{img_url}.{extension.split('.')[1]}"
                player_dob = collect_players_dob_from_all_eesl(player_eesl_id)
                player = {
                    "player_eesl_id": player_eesl_id,
                    "player_full_name": player_full_name,
                    "player_first_name": player_first_name,
                    "player_second_name": player_second_name,
                    "player_img_url": player_img_url,
                    "player_dob": player_dob
                }

                players_in_eesl.append(player.copy())
        except Exception as ex:
            print(ex)


if __name__ == '__main__':
    m = parse_all_players_from_eesl_and_create_jsons()
    # m = collect_players_dob_from_all_eesl(331)
    pprint(m)
