import logging

import httpx
from app.services.helpers import is_data_usable, stations_by_distance, days_with_data, rain_since

from app.constants import HTTP_TIMEOUT_SECONDS, MAX_STATION_ATTEMPTS, SMHI_BASE_URL, SMHI_API_URL, SMHI_RAIN_PARAMETER
from datetime import date

logger = logging.getLogger(__name__)


async def fetch_active_stations(param: str) -> list[dict]:
    url = f"{SMHI_BASE_URL}/parameter/{param}.json"
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        response = await client.get(url)
        response.raise_for_status()
        stations = response.json()["station"]

    return [
        {
            "id": s["key"],
            "name": s["name"],
            "latitude": s["latitude"],
            "longitude": s["longitude"],
        }
        for s in stations
        if s["active"] and s["measuringStations"] == "CORE"
    ]

async def fetch_rain_data(latitude: float, longitude: float) -> dict:
    """Fetch recent rain data from SMHI API for given coordinates.
    In: coordinates for the location the user has asked for
    Out: a dict with the rain data, summary over the last 7 and 14 days, and the station name where this was measured
    """
    active_stations = await fetch_active_stations(SMHI_RAIN_PARAMETER)

    fallback_station = None

    data_is_stale = True

    station = {}

    days = []

    candidates = stations_by_distance(active_stations, latitude, longitude)[:MAX_STATION_ATTEMPTS]



    # try to find a station with usable data, from the candidates list.
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        for station in candidates:
            url = SMHI_API_URL.format(param=SMHI_RAIN_PARAMETER, station_id=station["id"])
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPError as e:
                logger.warning("Error fetching data for station %s (ID: %s): %s", station["name"], station["id"], e)
                continue


            days = response.json().get("value", [])
            if not days:
                continue
            if fallback_station is None:
                fallback_station = (station, days)
            if is_data_usable(days):
                data_is_stale = False
                break
        #if no station is found use a fallback station and caveat it with the fact that the data is incomplete
        else: 
            if fallback_station is None:
                return {"error": "No nearby SMHI stations were found for this location"}
            station, days = fallback_station
            data_is_stale = True

        



    end_date = date.fromisoformat(days[-1]["ref"])



    return {
        "station": station["name"],
        "distance_km": station["distance_km"],
        "period_end": days[-1]["ref"],
        "days_with_data_14": days_with_data(days, end_date, 14),
        "rain_last_7_days_mm": rain_since(days, end_date, 7),
        "rain_last_14_days_mm": rain_since(days, end_date, 14),
        "data_is_stale": data_is_stale
    }