from src.seasons.schemas import SeasonSchemaCreate, SeasonSchemaUpdate
from src.sports.schemas import SportSchemaCreate
from src.tournaments.schemas import TournamentSchemaCreate


class TestData:
    @staticmethod
    def get_season_data() -> SeasonSchemaCreate:
        return SeasonSchemaCreate(year=2025, description="Test Season")

    @staticmethod
    def get_season_data_for_update() -> SeasonSchemaUpdate:
        return SeasonSchemaUpdate(year=2019, description="Updated Test Season")

    @staticmethod
    def get_sport_data() -> SportSchemaCreate:
        return SportSchemaCreate(title="Football", description="American Football")

    @staticmethod
    def get_tournament_data(season_id=None, sport_id=None) -> TournamentSchemaCreate:
        return TournamentSchemaCreate(
            tournament_eesl_id=111,
            title="Tournament A",
            description="Description of tournament A",
            tournament_logo_url="logo_url",
            tournament_logo_icon_url="icon_logo_url",
            tournament_logo_web_url="web_logo_url",
            season_id=season_id,
            sport_id=sport_id,
            sponsor_line_id=None,
            main_sponsor_id=None,
        )

    # You can add more test data methods as needed
    @staticmethod
    def get_alternative_tournament_data(
        season_id=None, sport_id=None
    ) -> TournamentSchemaCreate:
        return TournamentSchemaCreate(
            tournament_eesl_id=112,
            title="Tournament B",
            description="Description of tournament B",
            tournament_logo_url="alt_logo_url",
            tournament_logo_icon_url="alt_icon_logo_url",
            tournament_logo_web_url="alt_web_logo_url",
            season_id=season_id,
            sport_id=sport_id,
            sponsor_line_id=None,
            main_sponsor_id=None,
        )
