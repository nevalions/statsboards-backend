import factory
from src.core.models.sport import SportDB
from src.core.models.season import SeasonDB
from src.core.models.tournament import TournamentDB
from src.core.models.team import TeamDB
from src.core.models.person import PersonDB
from src.core.models.player import PlayerDB
from src.core.models.match import MatchDB
from tests.test_data import TestData
from src.sports.schemas import SportSchemaCreate
from src.seasons.schemas import SeasonSchemaCreate
from src.tournaments.schemas import TournamentSchemaCreate
from src.teams.schemas import TeamSchemaCreate
from src.person.schemas import PersonSchemaCreate
from src.player.schemas import PlayerSchemaCreate
from src.matches.schemas import MatchSchemaCreate


class SportFactorySample(factory.Factory):
    class Meta:
        model = SportDB

    title = factory.Sequence(lambda n: f"{TestData.get_sport_data().title}")
    description = factory.Sequence(lambda n: f"{TestData.get_sport_data().description}")


class SportFactoryAny(factory.Factory):
    class Meta:
        model = SportDB

    title = factory.Sequence(lambda n: f"{TestData.get_sport_data().title} + {n}")
    description = factory.Sequence(
        lambda n: f"{TestData.get_sport_data().description} + {n}"
    )


class SeasonFactorySample(factory.Factory):
    class Meta:
        model = SeasonDB

    year = factory.Sequence(lambda n: TestData.get_season_data().year)
    description = factory.Sequence(
        lambda n: f"{TestData.get_season_data().description}"
    )


class SeasonFactoryAny(factory.Factory):
    class Meta:
        model = SeasonDB

    year = factory.Sequence(lambda n: TestData.get_season_data().year + 10)
    description = factory.Sequence(
        lambda n: f"{TestData.get_season_data().description} + {n}"
    )


class TournamentFactory(factory.Factory):
    class Meta:
        model = TournamentDB

    tournament_eesl_id = factory.Sequence(lambda n: n + 100)
    title = factory.Sequence(lambda n: f"Tournament {n}")
    description = factory.Sequence(lambda n: f"Description for Tournament {n}")
    tournament_logo_url = factory.Sequence(lambda n: f"logo_url_{n}")
    tournament_logo_icon_url = factory.Sequence(lambda n: f"icon_url_{n}")
    tournament_logo_web_url = factory.Sequence(lambda n: f"web_url_{n}")
    sport_id = None
    season_id = None
    sponsor_line_id = None
    main_sponsor_id = None


class TeamFactory(factory.Factory):
    class Meta:
        model = TeamSchemaCreate

    team_eesl_id = factory.Sequence(lambda n: n + 1000)
    title = factory.Sequence(lambda n: f"Team {n}")
    description = factory.Sequence(lambda n: f"Description for Team {n}")
    team_logo_url = factory.Sequence(lambda n: f"team_logo_url_{n}")
    team_logo_icon_url = factory.Sequence(lambda n: f"team_icon_url_{n}")
    team_logo_web_url = factory.Sequence(lambda n: f"team_web_url_{n}")
    team_color = factory.Sequence(lambda n: f"color_{n}")
    city = factory.Sequence(lambda n: f"City {n}")
    sport_id = None
    sponsor_line_id = None
    main_sponsor_id = None


class PersonFactory(factory.Factory):
    class Meta:
        model = PersonSchemaCreate

    person_eesl_id = factory.Sequence(lambda n: n + 2000)
    first_name = factory.Sequence(lambda n: f"First{n}")
    second_name = factory.Sequence(lambda n: f"Second{n}")
    person_photo_url = factory.Sequence(lambda n: f"person_photo_url_{n}")
    person_photo_icon_url = factory.Sequence(lambda n: f"person_icon_url_{n}")
    person_photo_web_url = factory.Sequence(lambda n: f"person_web_url_{n}")
    person_dob = factory.LazyFunction(lambda: "2000-01-01")


class PlayerFactory(factory.Factory):
    class Meta:
        model = PlayerSchemaCreate

    player_eesl_id = factory.Sequence(lambda n: n + 3000)
    sport_id = None
    person_id = None


class MatchFactory(factory.Factory):
    class Meta:
        model = MatchSchemaCreate

    match_eesl_id = factory.Sequence(lambda n: n + 4000)
    match_date = factory.LazyFunction(lambda: "2025-01-01")
    week = factory.Sequence(lambda n: n + 1)
    tournament_id = None
    team_a_id = None
    team_b_id = None
    sponsor_line_id = None
    main_sponsor_id = None
