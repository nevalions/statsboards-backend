import asyncio
import os
from datetime import datetime
from pathlib import Path
from pprint import pprint
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import re

from src.core.config import uploads_path
from src.helpers import get_url
from src.helpers.file_service import file_service
from src.helpers.text_helpers import months, days
from src.pars_eesl.pars_settings import BASE_TOURNAMENT_URL


async def parse_tournament_matches_and_create_jsons(t_id: int):
    try:
        matches = await parse_tournament_matches_index_page_eesl(t_id)
        return matches
    except Exception as ex:
        print(ex)
        print(f"Something goes wrong, maybe no data in tournament id({t_id})")


async def parse_tournament_teams_and_create_jsons(t_id: int):
    try:
        teams = await parse_tournament_teams_index_page_eesl(t_id)
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

            image_path = os.path.join(uploads_path, f"teams/logos/{team_title}{ext}")
            relative_image_path = os.path.join("/static/uploads/teams/logos", f"{team_title}{ext}")
            # print(image_path)

            await file_service.download_image(team_logo_url, image_path)

            team_color = '#c01c28'
            try:
                team_color = await file_service.get_most_common_color(image_path) or team_color
            except Exception as err:
                print(f"Failed to get color for {team_logo_url}. Using default color #c01c28. Error: {err}")

            team = {
                "team_eesl_id": team_eesl_id,
                "title": team_title,
                "description": "",
                "team_logo_url": relative_image_path,
                "city": '',
                "team_color": team_color,
                "sport_id": 1,
            }
            teams_in_tournament.append(team.copy())

        except Exception as ex:
            print(ex)
    return teams_in_tournament


async def parse_tournament_matches_index_page_eesl(
        t_id: int, base_url: str = BASE_TOURNAMENT_URL, year: int = 2024
):
    week_counter = 0
    # first_week_num = None
    last_week_num = None
    matches_in_tournament = []
    url = f"{base_url}{str(t_id)}/calendar"
    req = get_url(url)
    soup = BeautifulSoup(req.content, "lxml")
    all_schedule_matches = soup.select(".js-schedule")

    for week in all_schedule_matches:
        try:
            all_weeks_in_schedule = week.find_all("div", class_="js-calendar-matches-header")
            for week_in_schedule in all_weeks_in_schedule:
                if week_in_schedule:
                    all_matches_in_week = week_in_schedule.find_all("ul", class_="schedule__matches-list")
                    date_texts = week_in_schedule.find("span", class_="schedule__head-text")
                    # print('DATE', date_texts.text.strip())

                    for mp in all_matches_in_week:
                        match = mp.find_all("li", class_="js-calendar-match")
                        for item in match:
                            match_eesl_id = int(
                                re.findall("\d+", item.find("a", class_="schedule__score").get("href"))[0])
                            team_a_id = int(item.find("a", class_="schedule__team-1").get("href").strip().split("=")[1])
                            team_b_id = int(item.find("a", class_="schedule__team-2").get("href").strip().split("=")[1])
                            game_time = item.find("span", class_="schedule__time").text.strip()
                            match_date = date_texts.text.strip()
                            date_formatted = match_date.replace(',', '') + " " + str(year) + " " + game_time

                            date, month, day, year, time = date_formatted.split()
                            month = months[month]
                            date_ = datetime.strptime(f"{date} {month} {year} {time}", "%d %B %Y %H:%M")
                            formatted_date = date_.strftime("%Y-%m-%d %H:%M:%S.%f")

                            iso_year, iso_week_num, iso_weekday = date_.isocalendar()

                            if last_week_num is None or last_week_num != iso_week_num:
                                week_counter += 1
                                last_week_num = iso_week_num

                            match_week = week_counter

                            # pprint([formatted_date, match_eesl_id, team_a_id, team_b_id, t_id])

                            match = {
                                "week": match_week,
                                "match_eesl_id": match_eesl_id,
                                "team_a_id": team_a_id,
                                "team_b_id": team_b_id,
                                "match_date": formatted_date,
                                "tournament_eesl_id": t_id,
                            }
                            pprint(match)
                            matches_in_tournament.append(match.copy())

        except Exception as ex:
            print(ex)
        return matches_in_tournament


async def main():
    m = await parse_tournament_matches_and_create_jsons(26)
    # m = parse_tournament_matches_and_create_jsons(19)
    pprint(m)


if __name__ == "__main__":
    asyncio.run(main())
