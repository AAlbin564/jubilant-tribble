from pydantic import BaseModel
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langgraph.prebuilt import ToolNode

from app.llm.tools import get_recent_weather_data, search_knowledge_base, recent_sightings
from app.llm.helpers import build_review_input, with_safety_note
from app.config import GEMINI_API_KEY, GEMINI_MODEL_NAME, VERIFIER_MODEL_NAME
from app.constants import (
    ASSISTANT_SYSTEM_MESSAGE, DEFAULT_REJECTION_ISSUE, LLM_MAX_RETRIES, LLM_TIMEOUT_SECONDS,
    MAX_REVISIONS, MAX_TOOL_ROUNDS, TOOL_LIMIT_MESSAGE, VERIFIER_SYSTEM_MESSAGE,
)


logger = logging.getLogger(__name__)


class AgentState(MessagesState):
    verifier_feedback: str
    num_of_revisions: int
    num_of_tool_rounds: int

class Verdict(BaseModel):
    approved:bool
    issues: list[str] = []

   

tools = [get_recent_weather_data, search_knowledge_base, recent_sightings]


assistant_model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL_NAME, api_key=GEMINI_API_KEY, timeout=LLM_TIMEOUT_SECONDS, max_retries=LLM_MAX_RETRIES,
)
# model without tools in case the model uses up its tool calling before it produces a draft
assistant_model_no_tools = assistant_model.bind_tools(tools, tool_choice="none")
assistant_model = assistant_model.bind_tools(tools)


verifier_model = ChatGoogleGenerativeAI(
    model=VERIFIER_MODEL_NAME, api_key=GEMINI_API_KEY,
    timeout=LLM_TIMEOUT_SECONDS, max_retries=LLM_MAX_RETRIES,
).with_structured_output(Verdict, method="json_schema")

async def run_verifier(review_input: str) -> Verdict | None:
    """Returns None if the verifier could not reach a verdict."""
    try:
        return await verifier_model.ainvoke([
            SystemMessage(VERIFIER_SYSTEM_MESSAGE),
            HumanMessage(review_input),
        ])
    except Exception:
        logger.exception("Verifier failed to produce a verdict")
        return None


async def assistant(state: AgentState):
    messages = [SystemMessage(ASSISTANT_SYSTEM_MESSAGE)] + state["messages"]
    if state.get("verifier_feedback"):
        messages.append(HumanMessage(
            f"[Reviewer feedback on your previous draft] {state['verifier_feedback']}. "
            "Fix these issues, using your tools if needed."
        ))

    model = assistant_model
    if state["num_of_tool_rounds"] >= MAX_TOOL_ROUNDS:
        logger.warning("Assistant used %s tool rounds; forcing an answer", MAX_TOOL_ROUNDS)
        messages.append(HumanMessage(TOOL_LIMIT_MESSAGE))
        model = assistant_model_no_tools

    response = await model.ainvoke(messages)
    if response.tool_calls:
        logger.info("Assistant → tools: %s", [(c["name"], c["args"]) for c in response.tool_calls])
        return {"messages": [response], "num_of_tool_rounds": state["num_of_tool_rounds"] + 1}

    logger.info("Assistant draft: %s", response.text[:300])
    return {"messages": [response]}

async def verifier(state: AgentState):
    draft = state["messages"][-1]
    verdict = await run_verifier(build_review_input(state["messages"]))

    if verdict is None:
        return {"verifier_feedback": "", "messages": [with_safety_note(draft)]}

    logger.info("Verifier approved=%s issues=%s", verdict.approved, verdict.issues)
    if verdict.approved:
        return {"verifier_feedback": ""}

    if state["num_of_revisions"] >= MAX_REVISIONS:
        logger.warning("Draft still rejected after %s revision(s); adding safety note", MAX_REVISIONS)
        return {"verifier_feedback": "", "messages": [with_safety_note(draft)]}

    issues = verdict.issues or [DEFAULT_REJECTION_ISSUE]
    return {
        "messages": [RemoveMessage(id=draft.id)],
        "verifier_feedback": "; ".join(issues),
        "num_of_revisions": state["num_of_revisions"] + 1,
    }

def build_lc_graph() -> CompiledStateGraph:

    def route_after_assistant(state: AgentState):
        if state["messages"][-1].tool_calls:
            return "tools"
        return "verifier"

    def route_after_verifier(state: AgentState):
        return "assistant" if state["verifier_feedback"] else END

    builder = StateGraph(AgentState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    builder.add_node("verifier", verifier)
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", route_after_assistant, ["tools", "verifier"])
    builder.add_edge("tools", "assistant")
    builder.add_conditional_edges("verifier", route_after_verifier, ["assistant", END])

    graph = builder.compile(checkpointer=InMemorySaver())

    return graph