import re

from src.core.enums import PeriodClockVariant

PERIOD_INDEX_RE = re.compile(r"(\d+)")


def extract_period_index(period_key: str | None, qtr: str | None) -> int:
    for value in (period_key, qtr):
        if not value:
            continue
        match = PERIOD_INDEX_RE.search(value)
        if match:
            return max(1, int(match.group(1)))
    return 1


def calculate_effective_gameclock_max(
    base_max: int | None,
    variant: PeriodClockVariant,
    period_index: int,
) -> int | None:
    if base_max is None:
        return None

    if variant == PeriodClockVariant.CUMULATIVE:
        return base_max * max(1, period_index)

    return base_max
