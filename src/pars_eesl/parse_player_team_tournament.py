from pprint import pprint

import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

from src.helpers import get_url
from src.pars_eesl.pars_settings import BASE_TOURNAMENT_URL


def parse_players_from_team_tournament_eesl_and_create_jsons(eesl_tournament_id, eesl_team_id):
    try:
        players = parse_players_from_team_tournament_eesl(eesl_tournament_id, eesl_team_id)
        print(len(players))
        return players
    except Exception as ex:
        print(ex)
        print(f'Something goes wrong, maybe no data')


def parse_players_from_team_tournament_eesl(eesl_tournament_id: int, eesl_team_id: int,
                                            base_url: str = BASE_TOURNAMENT_URL):
    players_in_eesl = []

    url = f'{base_url}{eesl_tournament_id}/teams/application?team_id={eesl_team_id}'
    req = get_url(url)
    soup = BeautifulSoup(req.content, 'lxml')
    all_eesl_players = soup.find_all('tr', class_='table__row')
    get_player_from_team_tournament_eesl(players_in_eesl, all_eesl_players, eesl_tournament_id, eesl_team_id)

    return players_in_eesl


def get_player_from_team_tournament_eesl(players_in_eesl, all_eesl_players, eesl_tournament_id, eesl_team_id):
    for ppp in all_eesl_players:
        try:
            player_eesl_id = int(re.findall(
                '\d+',
                ppp.find('a',
                         class_='table__player').get('href'))[0])
            player_number = ppp.find('td',
                                     class_='table__cell table__cell--number').text.strip().lower()
            player_position = ppp.find('td',
                                       class_='table__cell table__cell--amplua '
                                              'table__cell--amplua').text.strip().lower()
            player = {
                "eesl_tournament_id": eesl_tournament_id,
                "eesl_team_id": eesl_team_id,
                "player_eesl_id": player_eesl_id,
                "player_number": player_number,
                "player_position": player_position,
            }
            players_in_eesl.append(player.copy())
        except Exception as ex:
            print(ex)


if __name__ == '__main__':
    # m = parse_all_players_from_eesl_and_create_jsons()
    m = parse_players_from_team_tournament_eesl_and_create_jsons(19, 1)
    pprint(m)
