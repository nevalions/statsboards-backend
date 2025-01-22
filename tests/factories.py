import factory
from src.core.models.sport import SportDB
from src.core.models.season import SeasonDB
from src.core.models.tournament import TournamentDB
from tests.test_data import TestData


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
    sport_id = None  # NOT optional
    season_id = None  # NOT optional
    sponsor_line_id = None  # optional
    main_sponsor_id = None  # optional
