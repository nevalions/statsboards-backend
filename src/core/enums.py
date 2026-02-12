from enum import StrEnum


class ClockStatus(StrEnum):
    """Status values for gameclock and playclock."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"


class ClockDirection(StrEnum):
    """Direction the gameclock progresses."""

    DOWN = "down"
    UP = "up"


class ClockOnStopBehavior(StrEnum):
    """How the clock behaves when it is stopped."""

    HOLD = "hold"
    RESET = "reset"


class SportPeriodMode(StrEnum):
    """Period label mode used in sport scoreboard presets."""

    QTR = "qtr"
    PERIOD = "period"
    HALF = "half"
    SET = "set"
    INNING = "inning"
    CUSTOM = "custom"


class GameStatus(StrEnum):
    """Status values for match game state."""

    IN_PROGRESS = "in-progress"
    STOPPED = "stopped"
    STOPPING = "stopping"


class PlayerStartingType(StrEnum):
    """Player starting type values."""

    OFFENSE = "offense"
    DEFENSE = "defense"


class RussianMonth(StrEnum):
    """Russian month names for translation."""

    ЯНВАРЯ = "января"
    ФЕВРАЛЯ = "февраля"
    МАРТА = "марта"
    АПРЕЛЯ = "апреля"
    МАЯ = "мая"
    ИЮНЯ = "июня"
    ИЮЛЯ = "июля"
    АВГУСТА = "августа"
    СЕНТЯБРЯ = "сентября"
    ОКТЯБРЯ = "октября"
    НОЯБРЯ = "ноября"
    ДЕКАБРЯ = "декабря"
    ЯНВ = "янв"
    ФЕВ = "фев"
    МАР = "мар"
    АПР = "апр"
    МАЙ = "май"
    ИЮН = "июн"
    ИЮЛ = "июл"
    АВГ = "авг"
    СЕН = "сен"
    ОКТ = "окт"
    НОЯ = "ноя"
    ДЕК = "дек"


class RussianDay(StrEnum):
    """Russian day names for translation."""

    ПОНЕДЕЛЬНИК = "понедельник"
    ВТОРНИК = "вторник"
    СРЕДА = "среда"
    ЧЕТВЕРГ = "четверг"
    ПЯТНИЦА = "пятница"
    СУББОТА = "суббота"
    ВОСКРЕСЕНЬЕ = "воскресенье"
    ПОН = "пон"
    ВТО = "вто"
    СРЕ = "сре"
    ЧЕТ = "чет"
    ПЯТ = "пят"
    СУБ = "суб"
    ВОС = "вос"
