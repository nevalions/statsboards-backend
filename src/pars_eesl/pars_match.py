import asyncio
import logging
import re
from typing import TypedDict

from bs4 import BeautifulSoup
from fastapi import HTTPException

from src.helpers import get_url
from src.logging_config import setup_logging
from src.pars_eesl.pars_settings import BASE_MATCH_URL

setup_logging()
logger = logging.getLogger("backend_logger_parse_match_eesl")


class ParsedMatchPlayer(TypedDict):
    player_number: str
    player_position: str
    player_full_name: str
    player_first_name: str
    player_second_name: str
    player_eesl_id: int
    player_img_url: str | None
    player_team: str
    player_team_logo_url: str


class ParsedMatch(TypedDict):
    team_a: str
    team_b: str
    team_a_eesl_id: int | None
    team_b_eesl_id: int | None
    team_logo_url_a: str | None
    team_logo_url_b: str | None
    score_a: str
    score_b: str
    roster_a: list[ParsedMatchPlayer | None]
    roster_b: list[ParsedMatchPlayer | None]


async def parse_match_and_create_jsons(m_id: int):
    try:
        logger.debug(f"Parse match and create jsons for match id:{m_id}")
        data = await parse_match_index_page_eesl(m_id)
        return data
    except Exception as ex:
        logger.error(
            f"Error parse and create jsons for match id:{m_id} {ex}", exc_info=True
        )


async def parse_match_index_page_eesl(
    m_id: int, base_url: str = BASE_MATCH_URL
) -> ParsedMatch | None:
    try:
        match_data: ParsedMatch = {
            "team_a": "",
            "team_b": "",
            "team_a_eesl_id": None,
            "team_b_eesl_id": None,
            "team_logo_url_a": "",
            "team_logo_url_b": "",
            "score_a": "",
            "score_b": "",
            "roster_a": [],
            "roster_b": [],
        }

        logger.debug("Parse match from eesl")

        req = await get_url(base_url + str(m_id))
        soup = BeautifulSoup(req.content, "lxml")

        team_a = soup.find(
            "a", class_="match-protocol__team-name match-protocol__team-name--left"
        )

        team_b = soup.find(
            "a", class_="match-protocol__team-name match-protocol__team-name--right"
        )
        logo_urls = soup.find_all("img", class_="match-promo__team-img")
        score = soup.find("div", class_="match-promo__score-main")

        team_a_link = soup.find(
            "a", class_="match-protocol__team-name match-protocol__team-name--left"
        )
        team_b_link = soup.find(
            "a", class_="match-protocol__team-name match-protocol__team-name--right"
        )
        team_a_id = int(
            team_a_link.get("href").strip().split("=")[1]
            if team_a_link and team_a_link.get("href")
            else 0
        )
        team_b_id = int(
            team_b_link.get("href").strip().split("=")[1]
            if team_b_link and team_b_link.get("href")
            else 0
        )

        try:
            match_data["team_a"] = team_a.text.strip() if team_a else ""
            match_data["team_b"] = team_b.text.strip() if team_b else ""
            match_data["team_a_eesl_id"] = team_a_id
            match_data["team_b_eesl_id"] = team_b_id
            match_data["team_logo_url_a"] = logo_urls[0].get("src") if len(logo_urls) > 0 else None
            match_data["team_logo_url_b"] = logo_urls[1].get("src") if len(logo_urls) > 1 else None
            match_data["score_a"] = score.text.split(":")[0].strip() if score else ""
            match_data["score_b"] = score.text.split(":")[1].strip() if score else ""
        except Exception as ex:
            logger.error(f"Error with parsed match data {ex}", exc_info=True)

        players_a = soup.find_all(
            "li", class_="match-protocol__member match-protocol__member--left"
        )
        players_b = soup.find_all(
            "li", class_="match-protocol__member match-protocol__member--right"
        )

        roster_a: list[ParsedMatchPlayer | None] = []
        roster_b: list[ParsedMatchPlayer | None] = []
        if players_a:
            for p in players_a:
                try:
                    player = await get_player_eesl_from_match(
                        p, match_data["team_a"], match_data["team_logo_url_a"] or ""
                    )
                    if player:
                        roster_a.append(player.copy())
                except Exception as ex:
                    logger.error(
                        f"Error getting player for home roster {ex}", exc_info=True
                    )
        else:
            logger.warning(f"No home players found for match id:{m_id}")

        if players_b:
            for p in players_b:
                try:
                    player = await get_player_eesl_from_match(
                        p, match_data["team_b"], match_data["team_logo_url_b"] or ""
                    )
                    if player:
                        roster_b.append(player.copy())
                except Exception as ex:
                    logger.error(
                        f"Error getting player for away roster {ex}", exc_info=True
                    )
        else:
            logger.warning(f"No away players found for match id:{m_id}")

        try:
            logger.debug("Set sorted rosters")
            match_data["roster_a"] = sorted([d for d in roster_a if d], key=lambda d: d["player_number"] if d else "")
            match_data["roster_b"] = sorted([d for d in roster_b if d], key=lambda d: d["player_number"] if d else "")
        except Exception as ex:
            logger.error(f"Error getting sorted rosters {ex}", exc_info=True)

        return match_data
    except Exception as ex:
        logger.error(f"Error parsing match id:{m_id} {ex}", exc_info=True)
        return None


async def get_player_eesl_from_match(
    soup_player_team: BeautifulSoup, team: str, team_logo_url: str
) -> ParsedMatchPlayer | None:
    try:
        number_el = soup_player_team.find("span", class_="match-protocol__member-number")
        position_el = soup_player_team.find("span", class_="match-protocol__member-amplua")
        name_el = soup_player_team.find("a", class_="match-protocol__member-name")
        img_el = soup_player_team.find("img", class_="match-protocol__member-img")

        name_text = name_el.text.strip() if name_el else ""
        name_parts = name_text.split(" ") if name_text else []

        player: ParsedMatchPlayer = {
            "player_number": number_el.text.strip() if number_el else "",
            "player_position": position_el.text.strip() if position_el else "",
            "player_full_name": name_text,
            "player_first_name": name_parts[0] if len(name_parts) > 0 else "",
            "player_second_name": name_parts[1] if len(name_parts) > 1 else "",
            "player_eesl_id": int(
                re.findall(r"\d+", name_el.get("href") or "")[0]
            )
            if name_el and name_el.get("href")
            else 0,
            "player_img_url": img_el.get("src") if img_el else None,
            "player_team": team,
            "player_team_logo_url": team_logo_url,
        }
        if player:
            return player
        else:
            raise HTTPException(status_code=409, detail="Error parsing match player")
    except Exception as ex:
        logger.error(f"Error parsing match player {ex}", exc_info=True)
        return None


async def main():
    await parse_match_and_create_jsons(547)
    # print(m)


if __name__ == "__main__":
    asyncio.run(main())
