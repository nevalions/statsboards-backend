import factory
from src.core.models.sport import SportDB
from src.core.models.season import SeasonDB
from src.core.models.tournament import TournamentDB
from src.seasons.schemas import SeasonSchemaCreate
from src.sports.schemas import SportSchemaCreate
from tests.test_data import TestData


class SportFactory(factory.Factory):
    class Meta:
        model = SportDB

    # data: SportSchemaCreate = TestData.get_sport_data()

    title = factory.Sequence(lambda n: f"Football {n}")
    description = factory.Sequence(lambda n: f"American Football {n}")

    # title = factory.Sequence(lambda n: f"{SportFactory.data.title} {n}")
    # description = factory.Sequence(lambda n: f"{SportFactory.data.description} {n}")


class SeasonFactory(factory.Factory):
    class Meta:
        model = SeasonDB

    # data: SeasonSchemaCreate = TestData.get_season_data()

    year = factory.Sequence(lambda n: f"year {n}")
    description = factory.Sequence(lambda n: f"{n}")

    # year = factory.Sequence(lambda n: f"{SeasonFactory.data.year} {n}")
    # description = factory.Sequence(lambda n: f"{SeasonFactory.data.description} {n}")


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

    # IDs are automatically set from SubFactory instances
    sport_id = factory.LazyAttribute(lambda obj: obj.sport.id)
    season_id = factory.LazyAttribute(lambda obj: obj.season.id)
