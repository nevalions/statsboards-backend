from pprint import pprint

from bs4 import BeautifulSoup
import re

from statsboards_backend.helpers.request_services_helper import get_url
from statsboards_backend.pars_eesl.pars_settings import BASE_TOURNAMENT_URL


def parse_tournament_matches_and_create_jsons(t_id: int):
    try:
        matches = parse_tournament_matches_index_page_eesl(t_id)
        return matches
    except Exception as ex:
        print(ex)
        print(f'Something goes wrong, maybe no data in tournament id({t_id})')


def parse_tournament_teams_and_create_jsons(t_id: int):
    try:
        teams = parse_tournament_teams_index_page_eesl(t_id)
        return teams
    except Exception as ex:
        print(ex)
        print(f'Something goes wrong, maybe no data in tournament id({t_id})')


def parse_tournament_teams_index_page_eesl(
        t_id: int, base_url: str = BASE_TOURNAMENT_URL):
    teams_in_tournament = []
    url = f"{base_url}{str(t_id)}/teams"
    req = get_url(url)
    soup = BeautifulSoup(req.content, 'lxml')

    all_tournament_teams = soup.find_all('li', class_='teams__item')

    for t in all_tournament_teams:
        try:
            team = {
                "team_eesl_id": int(re.findall(
                    'team_id=(\d+)',
                    t.find('a',
                           class_='teams__logo').get('href'))[0]),
                "title": t.find('a',
                                class_='teams__name-link').text.strip().lower(),
                "description": '',
                "team_logo_url": t.find(
                    'img', alt=t.find(
                        'a', class_='teams__name-link').text.strip()).get('src')
            }
            teams_in_tournament.append(team.copy())
        except Exception as ex:
            print(ex)
    return teams_in_tournament


def parse_tournament_matches_index_page_eesl(
        t_id: int, base_url: str = BASE_TOURNAMENT_URL):
    matches_in_tournament = []
    url = f"{base_url}{str(t_id)}/calendar"
    req = get_url(url)
    soup = BeautifulSoup(req.content, 'lxml')
    all_tournament_matches = soup.select('.schedule__matches-item')

    for mp in all_tournament_matches:
        try:
            match = {
                "match_eesl_id": int(re.findall(
                    '\d+',
                    mp.find('a',
                            class_='schedule__score').get('href'))[0]),
                "eesl_id_team_a": int(mp.find('a',
                                              class_='schedule__team-1').get('href').
                                      strip().split('=')[1]),
                "eesl_id_team_b": int(mp.find('a',
                                              class_='schedule__team-2').get('href').
                                      strip().split('=')[1]),
                "tournament_eesl_id": t_id
            }
            matches_in_tournament.append(match.copy())
        except Exception as ex:
            print(ex)
    return matches_in_tournament


if __name__ == '__main__':
    # parse_tournament_teams_and_create_jsons(19)
    m = parse_tournament_matches_and_create_jsons(19)
    pprint(m)
