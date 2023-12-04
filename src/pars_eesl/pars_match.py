from bs4 import BeautifulSoup
import re

from src.helpers import get_url
from src.pars_eesl.pars_settings import BASE_MATCH_URL


def parse_match_and_create_jsons(m_id: int):
    # m_id = enter_match_id()
    try:
        data = parse_match_index_page_eesl(m_id)
        # save_match_data_to_json(data, str(m_id), DATA_DIR_ABSOLUTE)
        return data
    except Exception as ex:
        print(ex)
        print(f'Something goes wrong, maybe no data in match id({m_id})')


def enter_match_id():
    while True:
        try:
            m = input('Enter match id: ')
            if m.isdigit():
                return int(m)
            else:
                raise ValueError
        except Exception as ex:
            print(ex)
            print('Enter a valid match id')


def parse_match_index_page_eesl(m_id: int, base_url: str = BASE_MATCH_URL):
    """
    Parse match index page from eesl.pro
    Get:
    - home (a)team and away (b)team
    - score (a)team and score (b)team
    - roster (a) team and roster (b)team
    :param base_url:
    :param m_id:
    :return match_data: Dict with full match data
    """

    match_data = {
        'team_a': '',
        'team_b': '',
        'team_logo_url_a': '',
        'team_logo_url_b': '',
        'score_a': '',
        'score_b': '',
        'roster_a': [],
        'roster_b': [],
    }

    req = get_url(base_url + str(m_id))
    soup = BeautifulSoup(req.content, 'lxml')

    team_a = soup.find(
        'a', class_='match-protocol__team-name match-protocol__team-name--left')
    team_b = soup.find(
        'a', class_='match-protocol__team-name match-protocol__team-name--right')
    logo_urls = soup.find_all(
        'img', class_='match-promo__team-img')
    score = soup.find(
        'div', class_='match-promo__score-main')

    # print(team_a, team_b, logo_urls, score)

    match_data['team_a'] = team_a.text.strip()
    match_data['team_b'] = team_b.text.strip()
    match_data['team_logo_url_a'] = logo_urls[0].get('src')
    match_data['team_logo_url_b'] = logo_urls[1].get('src')
    match_data['score_a'] = score.text.split(':')[0].strip()
    match_data['score_b'] = score.text.split(':')[1].strip()

    players_a = soup.find_all(
        'li', class_='match-protocol__member match-protocol__member--left')
    players_b = soup.find_all(
        'li', class_='match-protocol__member match-protocol__member--right')

    roster_a = []
    roster_b = []

    for p in players_a:
        try:
            player = get_player_eesl_from_match(
                p,
                match_data['team_a'],
                match_data['team_logo_url_a'])
            roster_a.append(player.copy())
        except Exception as ex:
            print(ex)

    for p in players_b:
        try:
            player = get_player_eesl_from_match(
                p,
                match_data['team_b'],
                match_data['team_logo_url_b'])
            roster_b.append(player.copy())
        except Exception as ex:
            print(ex)

    match_data['roster_a'] = sorted(roster_a, key=lambda d: d['player_number'])
    match_data['roster_b'] = sorted(roster_b, key=lambda d: d['player_number'])

    return match_data


def get_player_eesl_from_match(
        soup_player_team: BeautifulSoup, team: str, team_logo_url: str):
    player = {
        'player_number': soup_player_team.find(
            'span', class_='match-protocol__member-number').text.strip(),
        'player_position': soup_player_team.find(
            'span', class_='match-protocol__member-amplua').text.strip(),
        'player_full_name': soup_player_team.find(
            'a', class_='match-protocol__member-name').text.strip(),
        'player_first_name': soup_player_team.find(
            'a', class_='match-protocol__member-name').text.strip().split(' ')[0],
        'player_second_name': soup_player_team.find(
            'a', class_='match-protocol__member-name').text.strip().split(' ')[1],
        'player_eesl_id': int(re.findall(
            '\d+',
            soup_player_team.find('a', class_='match-protocol__member-name').get('href'))[0]),
        'player_img_url': soup_player_team.find(
            'img', class_='match-protocol__member-img').get('src'),
        'player_team': team, 'player_team_logo_url': team_logo_url}

    return player


if __name__ == '__main__':
    m = parse_match_and_create_jsons(500)
    print(m)
