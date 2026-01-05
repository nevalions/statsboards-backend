from typing import TYPE_CHECKING

import factory

from src.matches.schemas import MatchSchemaCreate
from src.person.schemas import PersonSchemaCreate
from src.player.schemas import PlayerSchemaCreate
from src.positions.schemas import PositionSchemaCreate
from src.seasons.schemas import SeasonSchemaCreate
from src.sponsor_lines.schemas import SponsorLineSchemaCreate
from src.sponsors.schemas import SponsorSchemaCreate
from src.sports.schemas import SportSchemaCreate
from src.teams.schemas import TeamSchemaCreate
from src.tournaments.schemas import TournamentSchemaCreate
from tests.test_data import TestData

if TYPE_CHECKING:
    pass


class SportFactorySample(factory.Factory):
    class Meta:
        model = SportSchemaCreate

    title = factory.Sequence(lambda n: f"{TestData.get_sport_data().title}")
    description = factory.Sequence(lambda n: f"{TestData.get_sport_data().description}")


class SportFactoryAny(factory.Factory):
    class Meta:
        model = SportSchemaCreate

    title = factory.Sequence(lambda n: f"{TestData.get_sport_data().title} + {n}")
    description = factory.Sequence(lambda n: f"{TestData.get_sport_data().description} + {n}")


class SeasonFactorySample(factory.Factory):
    class Meta:
        model = SeasonSchemaCreate

    year = factory.Sequence(lambda n: TestData.get_season_data().year)
    description = factory.Sequence(lambda n: f"{TestData.get_season_data().description}")


class SeasonFactoryAny(factory.Factory):
    class Meta:
        model = SeasonSchemaCreate

    year = factory.Sequence(lambda n: TestData.get_season_data().year + 10)
    description = factory.Sequence(lambda n: f"{TestData.get_season_data().description} + {n}")


class TournamentFactory(factory.Factory):
    class Meta:
        model = TournamentSchemaCreate

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


class TournamentFactoryWithRelations(factory.Factory):
    class Meta:
        model = TournamentSchemaCreate

    tournament_eesl_id = factory.Sequence(lambda n: n + 100)
    title = factory.Sequence(lambda n: f"Tournament {n}")
    description = factory.Sequence(lambda n: f"Description for Tournament {n}")
    tournament_logo_url = factory.Sequence(lambda n: f"logo_url_{n}")
    tournament_logo_icon_url = factory.Sequence(lambda n: f"icon_url_{n}")
    tournament_logo_web_url = factory.Sequence(lambda n: f"web_url_{n}")
    sport_id = factory.SelfAttribute("sport.id")
    season_id = factory.SelfAttribute("season.id")
    sponsor_line_id = None
    main_sponsor_id = None
    sport = factory.SubFactory(SportFactoryAny)
    season = factory.SubFactory(SeasonFactoryAny)


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


class TeamFactoryWithRelations(factory.Factory):
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
    sport_id = factory.SelfAttribute("sport.id")
    sponsor_line_id = None
    main_sponsor_id = None
    sport = factory.SubFactory(SportFactoryAny)


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


class PlayerFactoryWithRelations(factory.Factory):
    class Meta:
        model = PlayerSchemaCreate

    player_eesl_id = factory.Sequence(lambda n: n + 3000)
    sport_id = factory.SelfAttribute("sport.id")
    person_id = factory.SelfAttribute("person.id")
    sport = factory.SubFactory(SportFactoryAny)
    person = factory.SubFactory(PersonFactory)


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


class MatchFactoryWithRelations(factory.Factory):
    class Meta:
        model = MatchSchemaCreate

    match_eesl_id = factory.Sequence(lambda n: n + 4000)
    match_date = factory.LazyFunction(lambda: "2025-01-01")
    week = factory.Sequence(lambda n: n + 1)
    tournament_id = factory.SelfAttribute("tournament.id")
    team_a_id = factory.SelfAttribute("team_a.id")
    team_b_id = factory.SelfAttribute("team_b.id")
    sponsor_line_id = None
    main_sponsor_id = None
    tournament = factory.SubFactory(TournamentFactoryWithRelations)
    team_a = factory.SubFactory(TeamFactoryWithRelations)
    team_b = factory.SubFactory(TeamFactoryWithRelations)


class PositionFactory(factory.Factory):
    class Meta:
        model = PositionSchemaCreate

    title = factory.Sequence(lambda n: f"Position {n}")
    sport_id = 1


class SponsorFactory(factory.Factory):
    class Meta:
        model = SponsorSchemaCreate

    title = factory.Sequence(lambda n: f"Sponsor {n}")
    logo_url = factory.Sequence(lambda n: f"logo_url_{n}")
    scale_logo = 1.0


class SponsorLineFactory(factory.Factory):
    class Meta:
        model = SponsorLineSchemaCreate

    title = factory.Sequence(lambda n: f"Sponsor Line {n}")
    is_visible = False


class UserFactory(factory.Factory):
    class Meta:
        model = "UserSchemaCreate"

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = "SecurePass123!"
    person_id = None
    is_active = True


class RoleFactory(factory.Factory):
    class Meta:
        model = "RoleSchemaCreate"

    name = "user"
    description = "Basic viewer role"
