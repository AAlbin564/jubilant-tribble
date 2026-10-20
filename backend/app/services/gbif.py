from collections import Counter
from datetime import date, timedelta

import httpx

from app.constants import MAX_DISTANCE, GBIF_OCCURRENCE_URL, GBIF_RESULT_LIMIT, GBIF_TIMEOUT_SECONDS

async def fetch_recent_sightings(
    species: str, latitude: float, longitude: float, days: int = 30
) -> dict:
    end = date.today()
    start = end - timedelta(days=days)
    params = {
        "scientificName": species,
        "country": "SE",
        "geoDistance": f"{latitude},{longitude},{MAX_DISTANCE}km",
        "eventDate": f"{start.isoformat()},{end.isoformat()}",
        "occurrenceStatus": "PRESENT",
        "limit": GBIF_RESULT_LIMIT,
    }
    async with httpx.AsyncClient(timeout=GBIF_TIMEOUT_SECONDS) as client:
        response = await client.get(GBIF_OCCURRENCE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    records = data.get("results", [])
    dates = sorted((r["eventDate"][:10] for r in records if r.get("eventDate")), reverse=True)
    places = Counter(r.get("municipality") or r.get("locality") or "unknown" for r in records)

    

    return {
        "species": species,
        "radius_km": MAX_DISTANCE,
        "period": f"{start.isoformat()} to {end.isoformat()}",
        "total_sightings": data.get("count", 0),
        "most_recent_dates": dates[:5],
        "top_areas": places.most_common(5),
        "note": "Citizen observations, mostly unvalidated. Absence of reports does not mean absence of the species.",
    }