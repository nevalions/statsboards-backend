from tests.test_data import TestData


def assert_season_equal(expected, actual):
    """Helper function to assert that two season objects are equal."""
    assert actual is not None
    assert actual.year == expected.year
    assert actual.description == expected.description
    assert actual.year != 2020
    assert actual.year == TestData.get_season_data().year
    assert actual.description == TestData.get_season_data().description
