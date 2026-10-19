import math
from datetime import date, timedelta
from app.constants import MAX_DATA_AGE_DAYS, MIN_DAYS_WITH_DATA

def distance_km(lat1, lon1, lat2, lon2) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def days_with_data(days: list[dict], end: date, num_days: int) -> int:
    start = end - timedelta(days=num_days - 1)
    return sum(1 for d in days if start <= date.fromisoformat(d["ref"]) <= end)

def is_data_fresh(days: list[dict]) -> bool:
    """check if data is fresh
    in: days value object retrieved from SMHI station
    Out: boolean representing if data has been added after threshold days"""
    if not days:
        return False

    latest_date = date.fromisoformat(days[-1]["ref"])
    return (date.today() - latest_date) <= timedelta(days=MAX_DATA_AGE_DAYS)

def is_data_usable(days: list[dict]) -> bool:
    if not is_data_fresh(days):
        return False
    end = date.fromisoformat(days[-1]["ref"])
    return days_with_data(days, end, 14) >= MIN_DAYS_WITH_DATA


def stations_by_distance(stations: list[dict], latitude: float, longitude: float) -> list[dict]:
    with_distance = [
        {**s, "distance_km": round(distance_km(s["latitude"], s["longitude"], latitude, longitude), 1)}
        for s in stations
    ]
    return sorted(with_distance, key=lambda s: s["distance_km"])

def rain_since(days: list[dict], end: date, num_days: int) -> float:
    start = end - timedelta(days=num_days - 1)
    return round(sum(
        float(d["value"]) for d in days
        if start <= date.fromisoformat(d["ref"]) <= end
    ), 1)

    