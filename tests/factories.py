import factory
from src.core.models.sport import SportDB
from src.core.models.season import SeasonDB
from src.core.models.tournament import TournamentDB
from tests.test_data import TestData


class SportFactory(factory.Factory):
    class Meta:
        model = SportDB

    title = factory.Sequence(lambda n: f"{TestData.get_sport_data().title}")
    description = factory.Sequence(lambda n: f"{TestData.get_sport_data().description}")


class SeasonFactory(factory.Factory):
    class Meta:
        model = SeasonDB

    year = factory.Sequence(lambda n: TestData.get_season_data().year)
    description = factory.Sequence(
        lambda n: f"{TestData.get_season_data().description}"
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

    # Foreign keys
    sport = factory.SubFactory(SportFactory)
    season = factory.SubFactory(SeasonFactory)

    sport_id = None
    season_id = None
