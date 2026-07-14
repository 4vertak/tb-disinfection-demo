
from zoneinfo import ZoneInfo
from datetime import date, datetime, time

LOCAL_TZ = ZoneInfo("Asia/Yakutsk")

def to_local(dt: datetime) -> datetime:
    """Перевод из UTC в локальное время"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(LOCAL_TZ)

def to_utc(dt: datetime) -> datetime:
    """Перевод локального времени в UTC"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(ZoneInfo("UTC"))

def get_period_dates(period, year):
    period_mapping = {
        "январь": (date(year, 1, 1), date(year, 1, 31)),
        "февраль": (date(year, 2, 1), date(year, 2, 28)),
        "март": (date(year, 3, 1), date(year, 3, 31)),
        "апрель": (date(year, 4, 1), date(year, 4, 30)),
        "май": (date(year, 5, 1), date(year, 5, 31)),
        "июнь": (date(year, 6, 1), date(year, 6, 30)),
        "июль": (date(year, 7, 1), date(year, 7, 31)),
        "август": (date(year, 8, 1), date(year, 8, 31)),
        "сентябрь": (date(year, 9, 1), date(year, 9, 30)),
        "октябрь": (date(year, 10, 1), date(year, 10, 31)),
        "ноябрь": (date(year, 11, 1), date(year, 11, 30)),
        "декабрь": (date(year, 12, 1), date(year, 12, 31)),
        "1-й квартал": (date(year, 1, 1), date(year, 3, 31)),
        "2-й квартал": (date(year, 4, 1), date(year, 6, 30)),
        "3-й квартал": (date(year, 7, 1), date(year, 9, 30)),
        "4-й квартал": (date(year, 10, 1), date(year, 12, 31)),
        "1-е полугодие": (date(year, 1, 1), date(year, 6, 30)),
        "2-е полугодие": (date(year, 7, 1), date(year, 12, 31)),
        "год": (date(year, 1, 1), date(year, 12, 31)),
    }

    start, end = period_mapping.get(period, (None, None))
    if start is None or end is None:
        return None, None

    # Возвращаем даты в локальной временной зоне
    start_local = datetime.combine(start, time.min, tzinfo=LOCAL_TZ)
    end_local = datetime.combine(end, time.max, tzinfo=LOCAL_TZ)

    return start_local, end_local

def get_available_years():
    """Получить список доступных годов для выбора"""
    current_year = datetime.now(LOCAL_TZ).year
    return [current_year - 2, current_year - 1, current_year]  # Можно расширить при необходимости