from fastapi import FastAPI, HTTPException
from typing import Annotated

import logging

from pydantic import BaseModel, StringConstraints

import app.config  # noqa: F401  loads .env and sets up logging before anything else
from app.constants import MAX_MESSAGE_LENGTH, MAX_THREAD_ID_LENGTH
from app.llm.graph import build_lc_graph

logger = logging.getLogger(__name__)


graph = build_lc_graph()

app = FastAPI()

NonEmptyString = Annotated[str, StringConstraints( strip_whitespace=True, min_length=1)]

class ChatRequest(BaseModel):
    thread_id: Annotated[NonEmptyString, StringConstraints(max_length=MAX_THREAD_ID_LENGTH)]
    text_content: Annotated[NonEmptyString, StringConstraints(max_length=MAX_MESSAGE_LENGTH)]

class ChatResponse(BaseModel):
    text_content: NonEmptyString

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}



@app.post("/api/chat", response_model=ChatResponse)

async def chat(chat_request: ChatRequest):

    
    config = {"configurable": {"thread_id": chat_request.thread_id}}
    try:
        result = await graph.ainvoke(
        {"messages": [("user", chat_request.text_content)], "verifier_feedback": "", "num_of_revisions": 0, "num_of_tool_rounds": 0},
        config,
        )
    except Exception:
        logger.exception("Graph invocation failed")
        raise HTTPException(status_code=502, detail="The AI service failed to respond. Try again.")
    return ChatResponse(text_content=result["messages"][-1].text)