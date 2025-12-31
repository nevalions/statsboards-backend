import logging
from pathlib import Path


logger = logging.getLogger("backend_logger_text_helpers")


months = {
    "января": "january",
    "февраля": "february",
    "марта": "march",
    "апреля": "april",
    "мая": "may",
    "июня": "june",
    "июля": "july",
    "августа": "august",
    "сентября": "september",
    "октября": "october",
    "ноября": "november",
    "декабря": "december",
    "янв": "jan",
    "фев": "feb",
    "мар": "mar",
    "апр": "apr",
    "май": "may",
    "июн": "jun",
    "июл": "jul",
    "авг": "aug",
    "сен": "sep",
    "окт": "oct",
    "ноя": "nov",
    "дек": "dec",
}

days = {
    "понедельник": "monday",
    "вторник": "tuesday",
    "среда": "wednesday",
    "четверг": "thursday",
    "пятница": "friday",
    "суббота": "saturday",
    "воскресенье": "sunday",
    "пон": "mon",
    "вто": "tue",
    "сре": "wed",
    "чет": "thu",
    "пят": "fri",
    "суб": "sat",
    "вос": "sun",
}


def ru_to_eng_datetime_month(ru: str) -> str | None:
    try:
        logger.debug(f"Converting ru to eng datetime month {ru}")
        s = ru.split(" ")
        eng_month = months[s[1]]
        return s[0] + " " + eng_month + " " + s[2]
    except Exception as ex:
        logger.error(
            f"Error converting ru to eng datetime month {ru} {ex}", exc_info=True
        )


def ru_to_eng_datetime_month_day_time(ru: str, year: str = "2023") -> str | None:
    try:
        logger.debug("Converting ru to eng datetime month day time")
        s = ru.strip().lower().split("/")
        day_num, month = s[0].strip().split(" ")
        day_word = s[1].strip()
        time = s[2].strip()
        eng_month = months[month]
        eng_day = days[day_word]
        return f"{year} {day_num} {eng_month} {eng_day} {time}"
    except Exception as ex:
        logger.error(
            f"Error converting ru to eng datetime month day time {ru} {ex}",
            exc_info=True,
        )


def safe_int_conversion(score_str: str) -> int:
    try:
        logger.debug(f"Safe converting to int {score_str}")
        return int(score_str.strip())
    except (ValueError, TypeError):
        logger.error(f"Error converting to int {score_str}")
        return 0


cyrillic_to_latin_map = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    "А": "A",
    "Б": "B",
    "В": "V",
    "Г": "G",
    "Д": "D",
    "Е": "E",
    "Ё": "Yo",
    "Ж": "Zh",
    "З": "Z",
    "И": "I",
    "Й": "Y",
    "К": "K",
    "Л": "L",
    "М": "M",
    "Н": "N",
    "О": "O",
    "П": "P",
    "Р": "R",
    "С": "S",
    "Т": "T",
    "У": "U",
    "Ф": "F",
    "Х": "H",
    "Ц": "Ts",
    "Ч": "Ch",
    "Ш": "Sh",
    "Щ": "Sch",
    "Ъ": "",
    "Ы": "Y",
    "Ь": "",
    "Э": "E",
    "Ю": "Yu",
    "Я": "Ya",
}


def convert_cyrillic_filename(filename: str) -> str:
    try:
        logger.debug(f"Converting cyrillic filename {filename} to latin")

        # Strip whitespace and check if empty
        filename = filename.strip()
        if not filename:
            logger.warning("Empty filename provided")
            return ""

        # Ensure idempotency: if already converted, return as-is
        if "_" not in filename and all(ord(c) < 127 for c in filename):
            # Filename appears to be already normalized (no underscores, only ASCII)
            # Check if it matches what would be converted
            converted = filename.replace(" ", "_")
            if converted == filename:
                logger.info(f"Filename unchanged: {filename}")
                return filename

        path = Path(filename)
        name = path.stem
        extension = path.suffix

        converted_name = ""
        for char in name:
            converted_name += cyrillic_to_latin_map.get(char, char)

        # Normalize spaces and replace with underscores
        converted_name_parts = [part for part in converted_name.split() if part]
        converted_name = "_".join(converted_name_parts)

        # Normalize extension (handle spaces in extension like " .txt")
        extension = extension.strip()
        if extension:
            extension = extension.replace(" ", "_").strip("_")

        # Reconstruct filename
        if extension:
            result = converted_name + extension
        else:
            result = converted_name

        # Final idempotency check
        if result == filename:
            logger.info(f"Filename unchanged: {filename}")
            return filename

        logger.info(f"Converted filename from {filename} to {result}")
        return result
    except Exception as ex:
        logger.error(
            f"Error converting cyrillic filename {filename} {ex}", exc_info=True
        )
        return filename


if __name__ == "__main__":
    print(ru_to_eng_datetime_month_day_time("22 Апреля / Суббота / 13:00"))
    print(convert_cyrillic_filename("команда.jpg"))
    print(convert_cyrillic_filename("Турнир 2023.png"))
    print(convert_cyrillic_filename("Фото команды.jpeg"))
