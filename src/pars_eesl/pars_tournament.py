import asyncio
import logging
import re
from datetime import datetime
from typing import List, Optional, TypedDict

from aiohttp import ClientError
from bs4 import BeautifulSoup

from src.helpers import get_url
from src.helpers.file_service import file_service
from src.helpers.text_helpers import months, safe_int_conversion
from src.logging_config import setup_logging
from src.pars_eesl.pars_settings import BASE_TOURNAMENT_URL

setup_logging()
logger = logging.getLogger("backend_logger_parser_eesl")
ITEM_PARSED = "TOURNAMENT"
ITEM_GOT = "TEAM"
ITEM_GOT_MATCH = "MATCH"


class ParsedMatchData(TypedDict):
    week: int
    match_eesl_id: int
    team_a_eesl_id: int
    team_b_eesl_id: int
    match_date: str
    tournament_eesl_id: int
    score_team_a: int
    score_team_b: int


class ParsedTeamData(TypedDict):
    team_eesl_id: int
    title: str
    description: str
    team_logo_url: str
    team_logo_icon_url: str
    team_logo_web_url: str
    city: str
    team_color: str
    sport_id: int


async def parse_tournament_matches_and_create_jsons(_id: int):
    logger.debug(
        f"Starting create parsed json of {ITEM_GOT_MATCH} for {ITEM_PARSED} id:{_id}"
    )
    try:
        data = await parse_tournament_matches_index_page_eesl(_id)
        logger.debug(f"Parsed json for {ITEM_PARSED} id{_id} data: {data}")
        return data
    except Exception as ex:
        logger.error(
            f"Something goes wrong with creating parsed json of {ITEM_GOT_MATCH}, "
            f"maybe no data in {ITEM_PARSED} id:{_id}, {ex}",
            exc_info=True,
        )
        return None


async def parse_tournament_teams_and_create_jsons(_id: int):
    logger.debug(
        f"Starting create parsed json of {ITEM_GOT} for {ITEM_PARSED} id:{_id}"
    )
    try:
        data = await parse_tournament_teams_index_page_eesl(_id)
        logger.debug(f"Parsed json for {ITEM_PARSED} id{_id} data: {data}")
        return data
    except Exception as ex:
        logger.error(
            f"Something goes wrong with creating parsed json of {ITEM_GOT}, "
            f"maybe no data in {ITEM_PARSED} id:{_id}, {ex}",
            exc_info=True,
        )
        return None


async def parse_tournament_teams_index_page_eesl(
    _id: int,
    base_url: str = BASE_TOURNAMENT_URL,
) -> Optional[List[ParsedTeamData]]:
    logger.debug(
        f"Starting parse for eesl {ITEM_PARSED} for {ITEM_GOT} id:{_id} url:{base_url}{_id}"
    )
    teams_in_tournament = []
    url = f"{base_url}{str(_id)}/teams"
    req = await get_url(url)
    # logger.debug(f"Request: {req}")
    soup = BeautifulSoup(req.content, "lxml")
    # logger.debug(f"Soup: {soup}")

    all_tournament_teams = soup.find_all("li", class_="teams__item")
    # logger.debug(f"All {ITEM_PARSED}'s {ITEM_GOT} html: {all_tournament_teams}")
    if all_tournament_teams:
        for t in all_tournament_teams:
            # logger.debug(f"Parsing {ITEM_GOT}: {t}")
            try:
                team_eesl_id = int(
                    re.findall(
                        r"team_id=(\d+)", t.find("a", class_="teams__logo").get("href")
                    )[0]
                )
                logger.debug(f"{ITEM_GOT} team_eesl_id: {team_eesl_id}")
                team_title = t.find("a", class_="teams__name-link").text.strip().lower()
                logger.debug(f"{ITEM_GOT} title: {team_title}")
                team_logo_url = t.find(
                    "img", alt=t.find("a", class_="teams__name-link").text.strip()
                ).get("src")
                logger.debug(f"{ITEM_GOT} logo url: {team_logo_url}")

                icon_image_height = 100
                web_view_image_height = 400

                image_info = await file_service.download_and_process_image(
                    img_url=team_logo_url,
                    image_type_prefix="teams/logos/",
                    image_title=team_title,
                    icon_height=icon_image_height,
                    web_view_height=web_view_image_height,
                )

                team_color = "#c01c28"
                try:
                    team_color = (
                        await file_service.get_most_common_color(
                            image_info["image_path"]
                        )
                        or team_color
                    )
                except Exception as ex:
                    logger.warning(
                        f"Failed to get color for {team_logo_url}. "
                        f"Using default color {team_color}. Error: {ex}",
                        exc_info=True,
                    )

                try:
                    final_team: ParsedTeamData = {
                        "team_eesl_id": team_eesl_id,
                        "title": team_title,
                        "description": "",
                        "team_logo_url": image_info["image_url"],
                        "team_logo_icon_url": image_info["image_icon_url"],
                        "team_logo_web_url": image_info["image_webview_url"],
                        "city": "",
                        "team_color": team_color,
                        "sport_id": 1,
                    }
                    logger.info(f"Final {ITEM_GOT} data: {final_team}")
                    teams_in_tournament.append(final_team.copy())
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
        logger.info(
            f"Parsed {ITEM_GOT}s for {ITEM_PARSED} id:{_id}: {teams_in_tournament}"
        )
        return teams_in_tournament
    else:
        logger.warning(f"No {ITEM_GOT}s found for eesl {ITEM_PARSED} id:{_id}")
        return None


def _parse_match_basic_info(item):
    match_eesl_id = int(
        re.findall(r"\d+", item.find("a", class_="schedule__score").get("href"))[0]
    )
    logger.debug(f"{ITEM_GOT_MATCH} match_eesl_id:{match_eesl_id}")
    
    team_a_eesl_id = int(
        item.find("a", class_="schedule__team-1").get("href").strip().split("=")[1]
    )
    logger.debug(f"{ITEM_GOT_MATCH} team_a_id:{team_a_eesl_id}")
    
    team_b_eesl_id = int(
        item.find("a", class_="schedule__team-2").get("href").strip().split("=")[1]
    )
    logger.debug(f"{ITEM_GOT_MATCH} team_b_id:{team_b_eesl_id}")
    
    score = item.find("div", class_="schedule__score-main").text.strip().split(":")
    logger.debug(f"{ITEM_GOT_MATCH} score:{score}")
    
    score_team_a = 0
    score_team_b = 0
    if len(score) == 2:
        score_team_a = safe_int_conversion(score[0])
        score_team_b = safe_int_conversion(score[1])
    
    logger.debug(f"{ITEM_GOT_MATCH} score_team_a:{score_team_a} - score_team_b:{score_team_b}")
    
    return {
        "match_eesl_id": match_eesl_id,
        "team_a_eesl_id": team_a_eesl_id,
        "team_b_eesl_id": team_b_eesl_id,
        "score_team_a": score_team_a,
        "score_team_b": score_team_b,
    }

def _parse_match_date(date_texts, item):
    game_time = item.find("span", class_="schedule__time").text.strip()
    logger.debug(f"{ITEM_GOT_MATCH} game_time:{game_time}")
    
    match_date = date_texts.text.strip()
    logger.debug(f"{ITEM_GOT_MATCH} match_date:{match_date}")
    
    date_formatted = match_date.replace(",", "") + " " + game_time
    logger.debug(f"{ITEM_GOT_MATCH} date_formatted:{date_formatted}")
    
    try:
        logger.debug(f"Split date_formatted:{date_formatted.split()}")
        date, month, day, time = date_formatted.split()
        logger.debug(f"{ITEM_GOT_MATCH} date:{date}, month:{month}, day:{day}, time:{time}")
    except Exception as ex:
        logger.error(f"Error splitting date_formatted:{date_formatted} {ex}")
        date = 1
        month = "января"
        year = 2024
        time = "12:00"
    
    month = months[month]
    date_ = datetime.strptime(f"{date} {month} {time}", "%d %B %H:%M")
    YEAR = 2025
    date_ = date_.replace(year=YEAR)
    formatted_date = date_.strftime("%Y-%m-%d %H:%M:%S.%f")
    
    return date_

def _calculate_week_number(date_, week_counter, last_week_num):
    iso_year, iso_week_num, iso_weekday = date_.isocalendar()
    logger.debug(f"Iso year: {iso_year}, iso week_num: {iso_week_num}, iso weekday: {iso_weekday}")
    
    if last_week_num is None or last_week_num != iso_week_num:
        logger.debug(f"Add new week for week_counter: {week_counter}+1")
        week_counter += 1
        last_week_num = iso_week_num
    
    return week_counter, last_week_num

def _create_final_match_data(match_info, match_week, formatted_date, tournament_id):
    final_match: ParsedMatchData = {
        "week": match_week,
        "match_eesl_id": match_info["match_eesl_id"],
        "team_a_eesl_id": match_info["team_a_eesl_id"],
        "team_b_eesl_id": match_info["team_b_eesl_id"],
        "match_date": formatted_date,
        "tournament_eesl_id": tournament_id,
        "score_team_a": match_info["score_team_a"],
        "score_team_b": match_info["score_team_b"],
    }
    logger.info(f"Final {ITEM_GOT_MATCH} data: {final_match}")
    return final_match

def _process_matches_in_week(mp_list, date_texts, week_counter, last_week_num, matches_in_tournament, tournament_id):
    for mp in mp_list:
        match = mp.find_all("li", class_="js-calendar-match")
        logger.debug(f"Getting {ITEM_GOT_MATCH} in week: {week_counter}")
        
        for item in match:
            match_info = _parse_match_basic_info(item)
            date_ = _parse_match_date(date_texts, item)
            week_counter, last_week_num = _calculate_week_number(date_, week_counter, last_week_num)
            formatted_date = date_.strftime("%Y-%m-%d %H:%M:%S.%f")
            
            final_match = _create_final_match_data(match_info, week_counter, formatted_date, tournament_id)
            matches_in_tournament.append(final_match.copy())
    
    return week_counter, last_week_num

async def parse_tournament_matches_index_page_eesl(
    _id: int, base_url: str = BASE_TOURNAMENT_URL, year: int = 2024
) -> Optional[List[ParsedMatchData]]:
    logger.debug(
        f"Starting parse for eesl {ITEM_PARSED} for {ITEM_GOT_MATCH} id:{_id} url:{base_url}{_id}"
    )
    week_counter = 0
    last_week_num = None
    matches_in_tournament = []
    
    url = f"{base_url}{str(_id)}/calendar"
    req = await get_url(url)
    soup = BeautifulSoup(req.content, "lxml")
    all_schedule_matches = soup.select(".js-schedule")
    
    for week in all_schedule_matches:
        logger.debug(f"Parsing week {week_counter} for {ITEM_PARSED} id:{_id}")
        try:
            all_weeks_in_schedule = week.find_all("div", class_="js-calendar-matches-header")
            logger.debug(f"Parsing all weeks: {all_weeks_in_schedule} for {ITEM_PARSED} id:{_id}")
            
            for week_in_schedule in all_weeks_in_schedule:
                logger.debug(f"Parsing week:{week_counter} for {ITEM_PARSED} id:{_id}")
                if not week_in_schedule:
                    continue
                    
                all_matches_in_week = week_in_schedule.find_all("ul", class_="schedule__matches-list")
                logger.debug(f"All {ITEM_GOT_MATCH}s in week in schedule: {week_in_schedule}")
                
                date_texts = week_in_schedule.find("span", class_="schedule__head-text")
                try:
                    logger.debug(f"Date of week:{week_counter} {date_texts.text.strip()}")
                except Exception as ex:
                    logger.debug(f"No date of week:{week_counter} date parsed:{date_texts} {ex}", exc_info=True)
                
                if len(all_matches_in_week) > 0:
                    week_counter, last_week_num = _process_matches_in_week(
                        all_matches_in_week, date_texts, week_counter, last_week_num, matches_in_tournament, _id
                    )
                else:
                    logger.warning(f"No {ITEM_GOT_MATCH}s found for week:{week}")
                    
        except Exception as ex:
            logger.error(f"Problem parsing {ITEM_GOT_MATCH} data for {ITEM_PARSED} id:{_id}, {ex}", exc_info=True)
            return None
    
    logger.info(f"Parsed {ITEM_GOT_MATCH}s for {ITEM_PARSED} id:{_id}: {matches_in_tournament}")
    return matches_in_tournament


#
# async def main():
#     m = await parse_tournament_teams_index_page_eesl(28)
#     # m = await parse_tournament_matches_and_create_jsons(26)
#     # m = parse_tournament_matches_and_create_jsons(19)
#     pprint(m)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
