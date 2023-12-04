from pprint import pprint

from bs4 import BeautifulSoup
import re

from statsboards_backend.helpers.request_services_helper import get_url
from statsboards_backend.pars_eesl.pars_settings import BASE_SEASON_URL


def parse_season_and_create_jsons(s_id: int):
    try:
        s_id = 7 # 2023
        data = parse_season_index_page_eesl(s_id)
        return data
    except Exception as ex:
        print(ex)
        print(f'Something goes wrong, maybe no data in season id({s_id})')


def parse_season_index_page_eesl(s_id: int, base_url: str = BASE_SEASON_URL):
    tournaments_in_season = []

    req = get_url(base_url + str(s_id))
    soup = BeautifulSoup(req.content, 'lxml')

    all_season_tournaments = soup.find_all('li', class_='tournaments-archive__item')
    for t in all_season_tournaments:
        try:
            tourn = {
                "tournament_eesl_id": int(re.findall(
                    '\d+',
                    t.find('a',
                           class_='tournaments-archive__link').get('href'))[0]),
                "title": t.find('a',
                                class_='tournaments-archive__link').get('title').strip(),
                "description": '',
                "tournament_logo_url": t.find('img',
                                              class_='tournaments-archive__img').get('src'),
                "fk_season": 2023}
            tournaments_in_season.append(tourn.copy())
        except Exception as ex:
            print(ex)
    return tournaments_in_season


if __name__ == '__main__':
    m = parse_season_and_create_jsons(7)
    print(m)
