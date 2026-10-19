from fastapi import FastAPI
from typing import Annotated, Literal

import logging

from pydantic import BaseModel, StringConstraints
from dotenv import load_dotenv

from app.llm.graph import build_lc_graph


logging.basicConfig(level=logging.INFO)

load_dotenv()


graph = build_lc_graph()

app = FastAPI()

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
    {"messages": [("user", chat_request.text_content)], "verifier_feedback": "", "num_of_revisions": 0},
    config,
    )
    return ChatResponse(text_content=result["messages"][-1].text)