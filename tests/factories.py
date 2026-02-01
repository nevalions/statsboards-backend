import random
from typing import TYPE_CHECKING

import factory

from src.matches.schemas import MatchSchemaCreate
from src.person.schemas import PersonSchemaCreate
from src.player.schemas import PlayerSchemaCreate
from src.player_team_tournament.schemas import PlayerTeamTournamentSchemaCreate
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

    title = factory.LazyFunction(lambda: f"{TestData.get_sport_data().title}")
    description = factory.LazyFunction(lambda: f"{TestData.get_sport_data().description}")


class SportFactoryAny(factory.Factory):
    class Meta:
        model = SportSchemaCreate

    title = factory.LazyFunction(
        lambda: f"{TestData.get_sport_data().title} + {random.randint(100000, 999999)}"
    )
    description = factory.LazyFunction(
        lambda: f"{TestData.get_sport_data().description} + {random.randint(100000, 999999)}"
    )


class SeasonFactorySample(factory.Factory):
    class Meta:
        model = SeasonSchemaCreate

    year = factory.LazyFunction(lambda: TestData.get_season_data().year)
    description = factory.LazyFunction(lambda: f"{TestData.get_season_data().description}")


class SeasonFactoryAny(factory.Factory):
    class Meta:
        model = SeasonSchemaCreate

    year = factory.LazyFunction(lambda: TestData.get_season_data().year)
    description = factory.LazyFunction(
        lambda: f"{TestData.get_season_data().description} {random.randint(100000, 999999)}"
    )


class TournamentFactory(factory.Factory):
    class Meta:
        model = TournamentSchemaCreate

    tournament_eesl_id = factory.LazyFunction(lambda: random.randint(1000000, 999999999))
    title = factory.LazyFunction(lambda: f"Tournament {random.randint(100000, 999999)}")
    description = factory.LazyFunction(
        lambda: f"Description for Tournament {random.randint(100000, 999999)}"
    )
    tournament_logo_url = factory.LazyFunction(
        lambda: f"logo_url_{random.randint(100000, 999999)}"
    )
    tournament_logo_icon_url = factory.LazyFunction(
        lambda: f"icon_url_{random.randint(100000, 999999)}"
    )
    tournament_logo_web_url = factory.LazyFunction(
        lambda: f"web_url_{random.randint(100000, 999999)}"
    )
    sport_id = None
    season_id = None
    sponsor_line_id = None
    main_sponsor_id = None


class TournamentFactoryWithRelations(factory.Factory):
    class Meta:
        model = TournamentSchemaCreate

    tournament_eesl_id = factory.LazyFunction(lambda: random.randint(1000000, 999999999))
    title = factory.LazyFunction(lambda: f"Tournament {random.randint(100000, 999999)}")
    description = factory.LazyFunction(
        lambda: f"Description for Tournament {random.randint(100000, 999999)}"
    )
    tournament_logo_url = factory.LazyFunction(
        lambda: f"logo_url_{random.randint(100000, 999999)}"
    )
    tournament_logo_icon_url = factory.LazyFunction(
        lambda: f"icon_url_{random.randint(100000, 999999)}"
    )
    tournament_logo_web_url = factory.LazyFunction(
        lambda: f"web_url_{random.randint(100000, 999999)}"
    )
    sport_id = factory.SelfAttribute("sport.id")
    season_id = factory.SelfAttribute("season.id")
    sponsor_line_id = None
    main_sponsor_id = None
    sport = factory.SubFactory(SportFactoryAny)
    season = factory.SubFactory(SeasonFactoryAny)


class TeamFactory(factory.Factory):
    class Meta:
        model = TeamSchemaCreate

    team_eesl_id = factory.LazyFunction(lambda: random.randint(10000000, 999999999))
    title = factory.LazyFunction(lambda: f"Team {random.randint(100000, 999999)}")
    description = factory.LazyFunction(lambda: f"Description for Team {random.randint(100000, 999999)}")
    team_logo_url = factory.LazyFunction(lambda: f"team_logo_url_{random.randint(100000, 999999)}")
    team_logo_icon_url = factory.LazyFunction(
        lambda: f"team_icon_url_{random.randint(100000, 999999)}"
    )
    team_logo_web_url = factory.LazyFunction(lambda: f"team_web_url_{random.randint(100000, 999999)}")
    team_color = factory.LazyFunction(lambda: random.choice(["red", "blue", "green", "yellow"]))
    city = factory.LazyFunction(lambda: f"City {random.randint(100000, 999999)}")
    sport_id = None
    sponsor_line_id = None
    main_sponsor_id = None


class TeamFactoryWithRelations(factory.Factory):
    class Meta:
        model = TeamSchemaCreate

    team_eesl_id = factory.LazyFunction(lambda: random.randint(10000000, 999999999))
    title = factory.LazyFunction(lambda: f"Team {random.randint(100000, 999999)}")
    description = factory.LazyFunction(lambda: f"Description for Team {random.randint(100000, 999999)}")
    team_logo_url = factory.LazyFunction(lambda: f"team_logo_url_{random.randint(100000, 999999)}")
    team_logo_icon_url = factory.LazyFunction(
        lambda: f"team_icon_url_{random.randint(100000, 999999)}"
    )
    team_logo_web_url = factory.LazyFunction(lambda: f"team_web_url_{random.randint(100000, 999999)}")
    team_color = factory.LazyFunction(lambda: random.choice(["red", "blue", "green", "yellow"]))
    city = factory.LazyFunction(lambda: f"City {random.randint(100000, 999999)}")
    sport_id = factory.SelfAttribute("sport.id")
    sponsor_line_id = None
    main_sponsor_id = None
    sport = factory.SubFactory(SportFactoryAny)


class PersonFactory(factory.Factory):
    class Meta:
        model = PersonSchemaCreate

    person_eesl_id = factory.LazyFunction(lambda: random.randint(1000000, 9999999))
    first_name = factory.LazyFunction(lambda: f"First{random.randint(100000, 999999)}")
    second_name = factory.LazyFunction(lambda: f"Second{random.randint(100000, 999999)}")
    person_photo_url = factory.LazyFunction(
        lambda: f"person_photo_url_{random.randint(100000, 999999)}"
    )
    person_photo_icon_url = factory.LazyFunction(
        lambda: f"person_icon_url_{random.randint(100000, 999999)}"
    )
    person_photo_web_url = factory.LazyFunction(
        lambda: f"person_web_url_{random.randint(100000, 999999)}"
    )
    person_dob = factory.LazyFunction(lambda: "2000-01-01")


class PlayerFactory(factory.Factory):
    class Meta:
        model = PlayerSchemaCreate

    player_eesl_id = factory.LazyFunction(lambda: random.randint(1000000, 9999999))
    sport_id = None
    person_id = None


class PlayerFactoryWithRelations(factory.Factory):
    class Meta:
        model = PlayerSchemaCreate

    player_eesl_id = factory.LazyFunction(lambda: random.randint(1000000, 9999999))
    sport_id = factory.SelfAttribute("sport.id")
    person_id = factory.SelfAttribute("person.id")
    sport = factory.SubFactory(SportFactoryAny)
    person = factory.SubFactory(PersonFactory)


class MatchFactory(factory.Factory):
    class Meta:
        model = MatchSchemaCreate

    match_eesl_id = factory.LazyFunction(lambda: random.randint(1000000, 999999999))
    match_date = factory.LazyFunction(lambda: "2025-01-01")
    week = factory.LazyFunction(lambda: random.randint(1, 52))
    tournament_id = None
    team_a_id = None
    team_b_id = None
    sponsor_line_id = None
    main_sponsor_id = None


class MatchFactoryWithRelations(factory.Factory):
    class Meta:
        model = MatchSchemaCreate

    match_eesl_id = factory.LazyFunction(lambda: random.randint(1000000, 999999999))
    match_date = factory.LazyFunction(lambda: "2025-01-01")
    week = factory.LazyFunction(lambda: random.randint(1, 52))
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

    title = factory.LazyFunction(lambda: f"Position {random.randint(100000, 999999)}")
    sport_id = 1


class SponsorFactory(factory.Factory):
    class Meta:
        model = SponsorSchemaCreate

    title = factory.LazyFunction(lambda: f"Sponsor {random.randint(100000, 999999)}")
    logo_url = factory.LazyFunction(lambda: f"logo_url_{random.randint(100000, 999999)}")
    scale_logo = 1.0


class SponsorLineFactory(factory.Factory):
    class Meta:
        model = SponsorLineSchemaCreate

    title = factory.LazyFunction(lambda: f"Sponsor Line {random.randint(100000, 999999)}")
    is_visible = False


class UserFactory(factory.Factory):
    class Meta:
        model = "UserSchemaCreate"

    username = factory.LazyFunction(lambda: f"user{random.randint(100000, 999999)}")
    email = factory.LazyFunction(lambda: f"user{random.randint(100000, 999999)}@example.com")
    password = "SecurePass123!"
    person_id = None
    is_active = True


class RoleFactory(factory.Factory):
    class Meta:
        model = "RoleSchemaCreate"

    name = "user"
    description = "Basic viewer role"


class PlayerTeamTournamentFactory(factory.Factory):
    class Meta:
        model = PlayerTeamTournamentSchemaCreate

    player_team_tournament_eesl_id = factory.LazyFunction(lambda: random.randint(100000, 999999999))
    player_id = None
    position_id = None
    team_id = None
    tournament_id = None
    player_number = "0"
