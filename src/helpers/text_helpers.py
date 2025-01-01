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


def ru_to_eng_datetime_month(ru):
    s = ru.split(" ")
    eng_month = months[s[1]]
    return s[0] + " " + eng_month + " " + s[2]


def ru_to_eng_datetime_month_day_time(ru, year="2023"):
    s = ru.strip().lower().split("/")
    day_num, month = s[0].strip().split(" ")
    day_word = s[1].strip()
    time = s[2].strip()
    eng_month = months[month]
    eng_day = days[day_word]
    return f"{year} {day_num} {eng_month} {eng_day} {time}"


def safe_int_conversion(score_str):
    try:
        # Try to convert the score to an integer
        return int(score_str.strip())
    except (ValueError, TypeError):
        # Return 0 if conversion fails
        return 0


if __name__ == "__main__":
    print(ru_to_eng_datetime_month_day_time("22 Апреля / Суббота / 13:00"))
