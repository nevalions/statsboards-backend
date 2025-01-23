from typing import List

from fastapi import HTTPException
from keyring.errors import ExceptionInfo

from src.seasons.schemas import SeasonSchemaCreate
from src.sports.schemas import SportSchemaCreate
from src.tournaments.schemas import TournamentSchemaCreate
from tests.test_data import TestData


def assert_http_exception_on_create(exc_info: ExceptionInfo):
    assert exc_info is not None
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 409
    assert "Error creating" in exc_info.value.detail
    assert "Check input data" in exc_info.value.detail


def assert_http_exception_on_update(exc_info: ExceptionInfo):
    assert exc_info is not None
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 409
    assert "Error updating" in exc_info.value.detail
    assert "Check input data" in exc_info.value.detail


def assert_http_exception_on_delete(exc_info: ExceptionInfo):
    assert exc_info is not None
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert "Failed to delete element" in exc_info.value.detail


def assert_season_equal(expected: SeasonSchemaCreate, actual: SeasonSchemaCreate):
    """Helper function to assert that two season objects are equal."""
    assert actual is not None
    assert expected is not None
    assert actual.year == expected.year
    assert actual.description == expected.description
    assert actual.year != 2020
    assert actual.year == TestData.get_season_data().year
    assert actual.description == TestData.get_season_data().description


def assert_sport_equal(expected: SportSchemaCreate, actual: SportSchemaCreate):
    """Helper function to assert that two sport objects are equal."""
    assert actual is not None
    assert expected is not None
    assert actual.title == expected.title
    assert actual.description == expected.description
    assert actual.title != "soccer"
    assert actual.title == TestData.get_sport_data().title
    assert actual.description == TestData.get_sport_data().description


def assert_tournament_equal(
    expected: TournamentSchemaCreate,
    actual: TournamentSchemaCreate,
    season: SeasonSchemaCreate,
    sport: SportSchemaCreate,
):
    """Helper function to assert that two tournament objects are equal."""
    assert actual is not None
    assert expected is not None
    assert season is not None
    assert sport is not None
    assert actual.season_id == expected.season_id
    assert actual.sport_id == expected.sport_id
    assert actual.title == expected.title
    assert actual.description == expected.description
    assert actual.tournament_logo_url == expected.tournament_logo_url
    assert actual.tournament_logo_icon_url == expected.tournament_logo_icon_url
    assert actual.tournament_logo_web_url == expected.tournament_logo_web_url
    assert actual.sponsor_line_id == expected.sponsor_line_id
    assert actual.main_sponsor_id == expected.main_sponsor_id
    assert sport.id == actual.sport_id
    assert season.id == actual.season_id
    assert sport.title == TestData.get_sport_data().title
    assert season.year == TestData.get_season_data().year


def assert_tournaments_equal(
    expected: List[TournamentSchemaCreate], actual: List[TournamentSchemaCreate]
):
    """Helper function to assert that number of tournament objects are equal."""
    assert len(actual) == len(expected)
    assert len(actual) != len(expected) - 1

    for i, fetched_tournament in enumerate(actual):
        expected_title = f"Tournament {i + 1}"
        assert fetched_tournament.title == expected_title, (
            f"Title mismatch: expected '{expected_title}', "
            f"got '{fetched_tournament.title}'"
        )
