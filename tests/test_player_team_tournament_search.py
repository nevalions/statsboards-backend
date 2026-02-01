import pytest

from src.person.db_services import PersonServiceDB
from src.player.db_services import PlayerServiceDB
from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
from src.player_team_tournament.schemas import (
    PaginatedPlayerTeamTournamentResponse,
    PaginatedPlayerTeamTournamentWithDetailsAndPhotosResponse,
)
from src.positions.db_services import PositionServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    PersonFactory,
    PlayerFactory,
    PlayerTeamTournamentFactory,
    PositionFactory,
    SeasonFactoryAny,
    SportFactoryAny,
    TeamFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
class TestPlayerTeamTournamentSearch:
    async def test_search_tournament_players_by_name(self, test_db):
        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        # Create required entities
        sport = await sport_service.create(SportFactoryAny.build())
        season = await season_service.create(SeasonFactoryAny.build())
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))

        # Create teams and persons with Cyrillic names
        team1 = await team_service.create(TeamFactory.build(sport_id=sport.id, title="Динамо Киев"))
        team2 = await team_service.create(
            TeamFactory.build(sport_id=sport.id, title="Спартак Москва")
        )

        person1 = await person_service.create(
            PersonFactory.build(first_name="Иван", second_name="Иванов")
        )
        person2 = await person_service.create(
            PersonFactory.build(first_name="Петр", second_name="Петров")
        )

        player1 = await player_service.create(
            PlayerFactory.build(person_id=person1.id, sport_id=sport.id)
        )
        player2 = await player_service.create(
            PlayerFactory.build(person_id=person2.id, sport_id=sport.id)
        )

        # Create player tournament associations
        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player1.id,
                team_id=team1.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="10",
            )
        )
        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player2.id,
                team_id=team2.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="11",
            )
        )

        # Search for "Иван" - substring search
        result = await player_team_tournament_service.search_tournament_players_with_pagination(
            tournament_id=tournament.id,
            search_query="Иван",
            skip=0,
            limit=10,
        )

        assert isinstance(result, PaginatedPlayerTeamTournamentResponse)
        # "Иван" appears in first_name of person1 and second_name of person1 ("Иванов")
        # So at least one result should match
        assert len(result.data) >= 1
        assert any(p.player_id == player1.id for p in result.data)
        assert result.metadata.total_items >= 1

    async def test_search_tournament_players_by_team(self, test_db):
        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        # Create required entities
        sport = await sport_service.create(SportFactoryAny.build())
        season = await season_service.create(SeasonFactoryAny.build())
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))

        team1 = await team_service.create(TeamFactory.build(sport_id=sport.id, title="Динамо Киев"))
        team2 = await team_service.create(
            TeamFactory.build(sport_id=sport.id, title="Спартак Москва")
        )

        person1 = await person_service.create(
            PersonFactory.build(first_name="Алексей", second_name="Смирнов")
        )
        person2 = await person_service.create(
            PersonFactory.build(first_name="Дмитрий", second_name="Смирнов")
        )

        player1 = await player_service.create(
            PlayerFactory.build(person_id=person1.id, sport_id=sport.id)
        )
        player2 = await player_service.create(
            PlayerFactory.build(person_id=person2.id, sport_id=sport.id)
        )

        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player1.id,
                team_id=team1.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="10",
            )
        )
        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player2.id,
                team_id=team2.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="11",
            )
        )

        # Search for person name (searches both first and second name)
        result = await player_team_tournament_service.search_tournament_players_with_pagination(
            tournament_id=tournament.id,
            search_query="Смирнов",
            skip=0,
            limit=10,
        )

        assert len(result.data) == 2
        assert all(p.team_id in [team1.id, team2.id] for p in result.data)

    async def test_search_tournament_players_by_number(self, test_db):
        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        # Create required entities
        sport = await sport_service.create(SportFactoryAny.build())
        season = await season_service.create(SeasonFactoryAny.build())
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        person1 = await person_service.create(
            PersonFactory.build(first_name="Alice", second_name="Johnson")
        )
        person2 = await person_service.create(
            PersonFactory.build(first_name="Bob", second_name="Smith")
        )

        player1 = await player_service.create(
            PlayerFactory.build(person_id=person1.id, sport_id=sport.id)
        )
        player2 = await player_service.create(
            PlayerFactory.build(person_id=person2.id, sport_id=sport.id)
        )

        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player1.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="10",
            )
        )
        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player2.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="11",
            )
        )

        # Search for player number "10" - should not match anything now (names only)
        result = await player_team_tournament_service.search_tournament_players_with_pagination(
            tournament_id=tournament.id,
            search_query="10",
            skip=0,
            limit=10,
        )

        assert len(result.data) == 0

    async def test_search_tournament_players_pagination(self, test_db):
        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        # Create required entities
        sport = await sport_service.create(SportFactoryAny.build())
        season = await season_service.create(SeasonFactoryAny.build())
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        # Create 25 players
        for i in range(25):
            person = await person_service.create(PersonFactory.build())
            player = await player_service.create(
                PlayerFactory.build(person_id=person.id, sport_id=sport.id)
            )
            await player_team_tournament_service.create(
                PlayerTeamTournamentFactory.build(
                    player_id=player.id,
                    team_id=team.id,
                    tournament_id=tournament.id,
                    position_id=position.id,
                    player_number=str(i),
                )
            )

        # Get first page
        page1 = await player_team_tournament_service.search_tournament_players_with_pagination(
            tournament_id=tournament.id,
            search_query=None,
            skip=0,
            limit=10,
        )

        assert len(page1.data) == 10
        assert page1.metadata.page == 1
        assert page1.metadata.has_next is True
        assert page1.metadata.has_previous is False
        assert page1.metadata.total_items == 25
        assert page1.metadata.total_pages == 3

        # Get second page
        page2 = await player_team_tournament_service.search_tournament_players_with_pagination(
            tournament_id=tournament.id,
            search_query=None,
            skip=10,
            limit=10,
        )

        assert len(page2.data) == 10
        assert page2.metadata.page == 2

    async def test_search_tournament_players_no_results(self, test_db):
        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        # Create required entities
        sport = await sport_service.create(SportFactoryAny.build())
        season = await season_service.create(SeasonFactoryAny.build())
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        person = await person_service.create(PersonFactory.build())
        player = await player_service.create(
            PlayerFactory.build(person_id=person.id, sport_id=sport.id)
        )

        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="10",
            )
        )

        # Test search that returns no results
        result = await player_team_tournament_service.search_tournament_players_with_pagination(
            tournament_id=tournament.id,
            search_query="NonExistent",
            skip=0,
            limit=10,
        )

        assert len(result.data) == 0
        assert result.metadata.total_items == 0
        assert result.metadata.total_pages == 0

    async def test_search_tournament_players_case_insensitive(self, test_db):
        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        # Create required entities
        sport = await sport_service.create(SportFactoryAny.build())
        season = await season_service.create(SeasonFactoryAny.build())
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))
        team = await team_service.create(
            TeamFactory.build(sport_id=sport.id, title="Manchester United")
        )

        person = await person_service.create(
            PersonFactory.build(first_name="John", second_name="Smith")
        )
        player = await player_service.create(
            PlayerFactory.build(person_id=person.id, sport_id=sport.id)
        )

        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="10",
            )
        )

        # Search with lowercase
        result = await player_team_tournament_service.search_tournament_players_with_pagination(
            tournament_id=tournament.id,
            search_query="john",
            skip=0,
            limit=10,
        )

        assert len(result.data) == 1

        # Search with uppercase
        result2 = await player_team_tournament_service.search_tournament_players_with_pagination(
            tournament_id=tournament.id,
            search_query="JOHN",
            skip=0,
            limit=10,
        )

        assert len(result2.data) == 1

    async def test_search_tournament_players_with_details(self, test_db):
        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        sport = await sport_service.create(SportFactoryAny.build())
        season = await season_service.create(SeasonFactoryAny.build())
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        position = await position_service.create(
            PositionFactory.build(sport_id=sport.id, title="Forward")
        )
        team = await team_service.create(TeamFactory.build(sport_id=sport.id, title="Test Team"))

        person = await person_service.create(
            PersonFactory.build(first_name="Test", second_name="Player")
        )
        player = await player_service.create(
            PlayerFactory.build(person_id=person.id, sport_id=sport.id)
        )

        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="99",
            )
        )

        result = (
            await player_team_tournament_service.search_tournament_players_with_pagination_details(
                tournament_id=tournament.id,
                search_query=None,
                skip=0,
                limit=10,
            )
        )

        assert len(result.data) == 1
        assert result.data[0].first_name == "Test"
        assert result.data[0].second_name == "Player"
        assert result.data[0].team_title == "Test Team"
        assert result.data[0].position_title.upper() == "FORWARD"
        assert result.data[0].player_number == "99"
        assert result.metadata.total_items == 1

    async def test_search_tournament_players_by_team_title(self, test_db):
        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        sport = await sport_service.create(SportFactoryAny.build())
        season = await season_service.create(SeasonFactoryAny.build())
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))

        team1 = await team_service.create(TeamFactory.build(sport_id=sport.id, title="Динамо Киев"))
        team2 = await team_service.create(
            TeamFactory.build(sport_id=sport.id, title="Спартак Москва")
        )

        person1 = await person_service.create(
            PersonFactory.build(first_name="Иван", second_name="Иванов")
        )
        person2 = await person_service.create(
            PersonFactory.build(first_name="Петр", second_name="Петров")
        )

        player1 = await player_service.create(
            PlayerFactory.build(person_id=person1.id, sport_id=sport.id)
        )
        player2 = await player_service.create(
            PlayerFactory.build(person_id=person2.id, sport_id=sport.id)
        )

        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player1.id,
                team_id=team1.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="10",
            )
        )
        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player2.id,
                team_id=team2.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="11",
            )
        )

        result = await player_team_tournament_service.search_tournament_players_with_pagination(
            tournament_id=tournament.id,
            search_query=None,
            team_title="Динамо",
            skip=0,
            limit=10,
        )

        assert len(result.data) == 1
        assert result.data[0].team_id == team1.id

    async def test_search_tournament_players_combined_filters(self, test_db):
        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        sport = await sport_service.create(SportFactoryAny.build())
        season = await season_service.create(SeasonFactoryAny.build())
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))

        team1 = await team_service.create(TeamFactory.build(sport_id=sport.id, title="Динамо Киев"))
        team2 = await team_service.create(
            TeamFactory.build(sport_id=sport.id, title="Спартак Москва")
        )

        person1 = await person_service.create(
            PersonFactory.build(first_name="Алексей", second_name="Смирнов")
        )
        person2 = await person_service.create(
            PersonFactory.build(first_name="Алексей", second_name="Петров")
        )

        player1 = await player_service.create(
            PlayerFactory.build(person_id=person1.id, sport_id=sport.id)
        )
        player2 = await player_service.create(
            PlayerFactory.build(person_id=person2.id, sport_id=sport.id)
        )

        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player1.id,
                team_id=team1.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="10",
            )
        )
        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player2.id,
                team_id=team2.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="11",
            )
        )

        result = await player_team_tournament_service.search_tournament_players_with_pagination(
            tournament_id=tournament.id,
            search_query="Смирнов",
            team_title="Динамо",
            skip=0,
            limit=10,
        )

        assert len(result.data) == 1
        assert result.data[0].player_id == player1.id
        assert result.data[0].team_id == team1.id

    async def test_search_tournament_players_with_pagination_details_and_photos(self, test_db):
        """Test that search_tournament_players_with_pagination_details_and_photos returns player data with photo fields."""
        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        team_service = TeamServiceDB(test_db)
        tournament_service = TournamentServiceDB(test_db)
        season_service = SeasonServiceDB(test_db)
        sport_service = SportServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        sport = await sport_service.create(SportFactoryAny.build())
        season = await season_service.create(SeasonFactoryAny.build())
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        position = await position_service.create(PositionFactory.build(sport_id=sport.id))

        team = await team_service.create(TeamFactory.build(sport_id=sport.id, title="Test Team"))

        person = await person_service.create(
            PersonFactory.build(
                first_name="Photo",
                second_name="Test",
                person_photo_url="/static/uploads/persons/photos/123.jpg",
                person_photo_icon_url="/static/uploads/persons/icons/123.jpg",
            )
        )

        player = await player_service.create(
            PlayerFactory.build(person_id=person.id, sport_id=sport.id)
        )

        await player_team_tournament_service.create(
            PlayerTeamTournamentFactory.build(
                player_id=player.id,
                team_id=team.id,
                tournament_id=tournament.id,
                position_id=position.id,
                player_number="99",
            )
        )

        result = await player_team_tournament_service.search_tournament_players_with_pagination_details_and_photos(
            tournament_id=tournament.id,
            search_query=None,
            skip=0,
            limit=10,
        )

        assert isinstance(result, PaginatedPlayerTeamTournamentWithDetailsAndPhotosResponse)
        assert len(result.data) == 1
        assert result.data[0].first_name == "Photo"
        assert result.data[0].second_name == "Test"
        assert result.data[0].team_title == "Test Team"
        assert result.data[0].position_title == position.title
        assert result.data[0].player_number == "99"
        assert result.data[0].person_photo_url == "/static/uploads/persons/photos/123.jpg"
        assert result.data[0].person_photo_icon_url == "/static/uploads/persons/icons/123.jpg"
        assert result.metadata.total_items == 1
