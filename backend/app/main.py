from fastapi import FastAPI, HTTPException
from typing import Annotated, Literal
from pydantic import BaseModel, StringConstraints
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.vectorstores import InMemoryVectorStore
from app.services.geocoding import geocode_location
from app.services.smhi import fetch_rain_data
import httpx
import logging
import os

logger = logging.getLogger(__name__)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in the environment variables.")






system_message = "You are a helpful assistant with the goal of helping users with knowledge of mushrooms."





@tool
async def get_recent_weather_data(location: str) -> dict:
    """Get recent rain data near a Swedish location,
    from SMHI's quality-checked weather stations.
    
    Use this when the user asks about the weather in a specific location. Do not use this for forecasts and locations outside sweden.

    Args: location: a Swedish town or place name e.g. "Stockholm" or "Lövön"
    
    The results name station and its distance to the given location, and the date the data runs to. if the data_is_stale flag is true
    inform the user that the data may be incomplete or out of date"""
    param = {
        "rain": 5,
        "temperature": 2,
        "location": location
    }

    location_data = await geocode_location(location)
    if location_data is None:
        return {"error": f"Location '{location}' could not be found in Sweden."}
    rain = await fetch_rain_data(location_data["latitude"], location_data["longitude"])

    return {
        "location": location_data,
        "rain": rain
    }

#model and graph setup

tools = [get_recent_weather_data]

model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", api_key=GEMINI_API_KEY)

model = model.bind_tools(tools)

async def assistant(state: MessagesState):
    messages = [SystemMessage(system_message)] + state["messages"]
    response = await model.ainvoke(messages)
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

graph = builder.compile(checkpointer=InMemorySaver())

app = FastAPI()


@app.get("/api/test")
async def test_endpoint():
    return await fetch_rain_data(59.3293, 18.0686)  # Example coordinates for Stockholm

NonEmptyString = Annotated[str, StringConstraints( strip_whitespace=True, min_length=1)]

RoleTypes = Literal["user", "assistant"]

class Message(BaseModel):
    role: RoleTypes
    text_content: NonEmptyString

class ChatRequest(BaseModel):
    thread_id: Annotated[NonEmptyString, StringConstraints(max_length=64)]
    text_content: Annotated[NonEmptyString, StringConstraints(max_length=2000)]

class ChatResponse(BaseModel):
    text_content: NonEmptyString

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}



@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):

    
    config = {"configurable": {"thread_id": chat_request.thread_id}}
    result = await graph.ainvoke(
        {"messages": [("user", chat_request.text_content)]},
        config,
    )
    return ChatResponse(text_content=result["messages"][-1].text)