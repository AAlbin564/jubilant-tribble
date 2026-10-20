
from langchain_core.tools import tool
import logging

from app.services.geocoding import geocode_location
from app.services.smhi import fetch_rain_data
from app.config import GEMINI_API_KEY
from app.rag.knowledge_base import get_vector_store
from app.rag.helpers import to_result
from app.services.gbif import fetch_recent_sightings
from app.constants import SEARCH_RESULTS

logger = logging.getLogger(__name__)



vector_store = get_vector_store(GEMINI_API_KEY)

@tool 
def search_knowledge_base(query:str) -> list[dict]:
    """Search a knowledge base of Wikipedia articles about mushroom species found in Sweden.

    Use this for any questions about mushroom species. Always mention the source URL of the facts you use.
    
        Args: the query to look up e.g. "edibale mushrooms" 
    """
    logger.info("Knowledge base searched for %s", query)

    results = vector_store.similarity_search(query, k=SEARCH_RESULTS)
    return [to_result(doc) for doc in results]

@tool 
async def recent_sightings(species, location, days=30):
    """Provides up to date data with for mushroom sightings around a Swedish location.
    
    Use this when the user asks for information related to a species and a location.
    
        Args: a species a location and a specified number of days to check the default of which is 30. 
        The species name must be its scientific name e.g Craterellus tubaeformis not Winter Chantarelle
    """

    logger.info("sightings tool called for %s", location)

    location_data = await geocode_location(location)
    if location_data is None:
        return {"error": f"Location '{location}' could not be found in Sweden."}

    result = await fetch_recent_sightings(species, location_data["latitude"], location_data["longitude"], days)

    return result


@tool
async def get_recent_weather_data(location: str) -> dict:
    """Get recent rain data near a Swedish location,
    from SMHI's quality-checked weather stations.
    
    Use this when the user asks about the weather in a specific location. Do not use this for forecasts and locations outside sweden.

        Args: location: a Swedish town or place name e.g. "Stockholm" or "Lövön"
    
    The results name station and its distance to the given location, and the date the data runs to. if the data_is_stale flag is true
    inform the user that the data may be incomplete or out of date"""
    logger.info("Weather tool called for %s", location)

    location_data = await geocode_location(location)
    if location_data is None:
        return {"error": f"Location '{location}' could not be found in Sweden."}
    rain = await fetch_rain_data(location_data["latitude"], location_data["longitude"])

    return {
        "location": location_data,
        "rain": rain
    }