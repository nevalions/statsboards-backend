import asyncio
import logging
from typing import TypedDict, Optional, List

from bs4 import BeautifulSoup
import re

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
    team_a_eesl_id: int
    team_b_eesl_id: int
    team_logo_url_a: str | None
    team_logo_url_b: str | None
    score_a: str
    score_b: str
    roster_a: list[Optional[ParsedMatchPlayer]]
    roster_b: list[Optional[ParsedMatchPlayer]]


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
) -> Optional[ParsedMatch]:
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

        logger.debug(f"Parse match from eesl")

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

        team_a_id = int(
            soup.find(
                "a", class_="match-protocol__team-name match-protocol__team-name--left"
            )
            .get("href")
            .strip()
            .split("=")[1]
        )
        team_b_id = int(
            soup.find(
                "a", class_="match-protocol__team-name match-protocol__team-name--right"
            )
            .get("href")
            .strip()
            .split("=")[1]
        )

        try:
            match_data["team_a"] = team_a.text.strip()
            match_data["team_b"] = team_b.text.strip()
            match_data["team_a_eesl_id"] = team_a_id
            match_data["team_b_eesl_id"] = team_b_id
            match_data["team_logo_url_a"] = logo_urls[0].get("src")
            match_data["team_logo_url_b"] = logo_urls[1].get("src")
            match_data["score_a"] = score.text.split(":")[0].strip()
            match_data["score_b"] = score.text.split(":")[1].strip()
        except Exception as ex:
            logger.error(f"Error with parsed match data {ex}", exc_info=True)

        players_a = soup.find_all(
            "li", class_="match-protocol__member match-protocol__member--left"
        )
        players_b = soup.find_all(
            "li", class_="match-protocol__member match-protocol__member--right"
        )

        roster_a: List[Optional[ParsedMatchPlayer]] = []
        roster_b: List[Optional[ParsedMatchPlayer]] = []
        if players_a:
            for p in players_a:
                try:
                    player = await get_player_eesl_from_match(
                        p, match_data["team_a"], match_data["team_logo_url_a"]
                    )
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
                        p, match_data["team_b"], match_data["team_logo_url_b"]
                    )
                    roster_b.append(player.copy())
                except Exception as ex:
                    logger.error(
                        f"Error getting player for away roster {ex}", exc_info=True
                    )
        else:
            logger.warning(f"No away players found for match id:{m_id}")

        try:
            logger.debug(f"Set sorted rosters")
            match_data["roster_a"] = sorted(roster_a, key=lambda d: d["player_number"])
            match_data["roster_b"] = sorted(roster_b, key=lambda d: d["player_number"])
        except Exception as ex:
            logger.error(f"Error getting sorted rosters {ex}", exc_info=True)

        return match_data
    except Exception as ex:
        logger.error(f"Error parsing match id:{m_id} {ex}", exc_info=True)


async def get_player_eesl_from_match(
    soup_player_team: BeautifulSoup, team: str, team_logo_url: str
) -> Optional[ParsedMatchPlayer]:
    try:
        player: ParsedMatchPlayer = {
            "player_number": soup_player_team.find(
                "span", class_="match-protocol__member-number"
            ).text.strip(),
            "player_position": soup_player_team.find(
                "span", class_="match-protocol__member-amplua"
            ).text.strip(),
            "player_full_name": soup_player_team.find(
                "a", class_="match-protocol__member-name"
            ).text.strip(),
            "player_first_name": soup_player_team.find(
                "a", class_="match-protocol__member-name"
            )
            .text.strip()
            .split(" ")[0],
            "player_second_name": soup_player_team.find(
                "a", class_="match-protocol__member-name"
            )
            .text.strip()
            .split(" ")[1],
            "player_eesl_id": int(
                re.findall(
                    r"\d+",
                    soup_player_team.find(
                        "a", class_="match-protocol__member-name"
                    ).get("href"),
                )[0]
            ),
            "player_img_url": soup_player_team.find(
                "img", class_="match-protocol__member-img"
            ).get("src"),
            "player_team": team,
            "player_team_logo_url": team_logo_url,
        }
        if player:
            return player
        else:
            raise HTTPException(status_code=409, detail=f"Error parsing match player")
    except Exception as ex:
        logger.error(f"Error parsing match player {ex}", exc_info=True)


async def main():
    m = await parse_match_and_create_jsons(547)
    # print(m)


if __name__ == "__main__":
    asyncio.run(main())
