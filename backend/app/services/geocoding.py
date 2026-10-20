import httpx

from app.constants import GEOCODING_API_URL, HTTP_TIMEOUT_SECONDS

async def geocode_location(location: str) -> dict | None:
    """Get coordinates for a Swedish location name. Returns None if not found."""
    params = {"name": location, "count": 1, "language": "sv", "countryCode": "SE"}
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        response = await client.get(GEOCODING_API_URL, params=params)
        response.raise_for_status()
        results = response.json().get("results")

    if not results:
        return None

    place = results[0]
    return {
        "name": place["name"],
        "county": place.get("admin1"),
        "latitude": place["latitude"],
        "longitude": place["longitude"],
    }