import asyncio
import logging
import re
from pprint import pprint
from typing import TypedDict

from bs4 import BeautifulSoup
from fastapi import HTTPException

from src.helpers import get_url
from src.pars_eesl.pars_settings import BASE_TOURNAMENT_URL

logger = logging.getLogger("backend_logger_parse_players_from_team_tournament_eesl")


class ParsedPlayerTeamTournament(TypedDict):
    eesl_tournament_id: int
    eesl_team_id: int
    player_eesl_id: int
    player_number: str
    player_position: str


async def parse_players_from_team_tournament_eesl_and_create_jsons(
    eesl_tournament_id, eesl_team_id
):
    try:
        logger.debug("Parse and create json players from team_tournament eesl")
        players = await parse_players_from_team_tournament_eesl(eesl_tournament_id, eesl_team_id)
        logger.debug(f"Parse number of players from team_tournament {len(players)}")
        return players
    except Exception as ex:
        logger.error(
            f"Error on parsing and saving json players from team_tournament eesl: {ex}",
            exc_info=True,
        )
        raise
        return None


async def parse_players_from_team_tournament_eesl(
    eesl_tournament_id: int, eesl_team_id: int, base_url: str = BASE_TOURNAMENT_URL
):
    players_in_eesl: list[ParsedPlayerTeamTournament] = []
    logger.debug(f"Parse players from team_tournament eesl {eesl_team_id}")
    try:
        url = f"{base_url}{eesl_tournament_id}/teams/application?team_id={eesl_team_id}"
        logger.debug(f"URL: {url}")
        req = await get_url(url)
        soup = BeautifulSoup(req.content, "lxml")
        all_eesl_players = soup.find_all("tr", class_="table__row")
        try:
            await get_player_from_team_tournament_eesl(
                players_in_eesl, all_eesl_players, eesl_tournament_id, eesl_team_id
            )
        except Exception as ex:
            logger.error(
                f"Error on getting player from  parsed team_tournament eesl: {ex}",
                exc_info=True,
            )

        return players_in_eesl
    except Exception as ex:
        logger.error(f"Error on parsing players from team_tournament eesl: {ex}", exc_info=True)
        raise


async def get_player_from_team_tournament_eesl(
    players_in_eesl, all_eesl_players, eesl_tournament_id, eesl_team_id
) -> list[ParsedPlayerTeamTournament] | None:
    try:
        if all_eesl_players:
            for ppp in all_eesl_players:
                try:
                    player_eesl_id = int(
                        re.findall(r"\d+", ppp.find("a", class_="table__player").get("href"))[0]
                    )
                    logger.debug(f"Got player eesl id: {player_eesl_id}")
                    player_number = (
                        ppp.find("td", class_="table__cell table__cell--number")
                        .text.strip()
                        .lower()
                    )
                    logger.debug(f"Got player number: {player_number}")
                    player_position = (
                        ppp.find(
                            "td",
                            class_="table__cell table__cell--amplua table__cell--amplua",
                        )
                        .text.strip()
                        .lower()
                    )
                    logger.debug(f"Got player position: {player_position}")
                    player: ParsedPlayerTeamTournament = {
                        "eesl_tournament_id": eesl_tournament_id,
                        "eesl_team_id": eesl_team_id,
                        "player_eesl_id": player_eesl_id,
                        "player_number": player_number,
                        "player_position": player_position,
                    }
                    logger.debug(f"Got final player: {player}")
                    players_in_eesl.append(player.copy())
                except Exception as ex:
                    logger.error(
                        f"Error on parsing player from team_tournament eesl: {ex}",
                        exc_info=True,
                    )
            return players_in_eesl
        else:
            raise HTTPException(status_code=404, detail="Parsed eesl players empty")
    except Exception as ex:
        logger.error(f"Error on parsing player from team_tournament eesl: {ex}", exc_info=True)
        return None


async def main():
    m = await parse_players_from_team_tournament_eesl_and_create_jsons(19, 1)
    pprint(m)


if __name__ == "__main__":
    asyncio.run(main())
