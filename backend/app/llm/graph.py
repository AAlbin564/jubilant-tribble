from pydantic import BaseModel
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import ToolMessage

from app.llm.tools import get_recent_weather_data, search_knowledge_base
from app.config import GEMINI_API_KEY
from app.constants import MAX_REVISIONS

logger = logging.getLogger(__name__)

assistant_system_message = "You are a helpful assistant with the goal of helping users with knowledge of mushrooms."

verifier_system_message = """You are a safety expert and fact checking analyst with the goal of making sure that drafts that 
reaches people contains information that is safe and meets certain guidelines. You are to either reject or approve based on these safety guidelines
you are not to make judgements on style or tone. 

As an input you will recieve the users question the evidence the assistant gathered from their tools and the assistants draft
    
    Safety guidelines: 
    1.Make sure that dangerous Lookalikes are always mentioned, when a specific mushroom is being discussed in detail.
    2.Ask them to confer with a mushroom expert if trying to identify a mushroom.
    3.Make sure that they cite the sources when these use the knowledge base. 
    4. do not provide instructions for preparing or cooking a toxic mushroom
    5. if the weather data is marked stale or incomplete the assistant must provide this information
    6. Species facts in the draft must be supported by the evidence. Flag any that are not.

    Approve the draft if it follows all the guidelines.
    Each issue must say exactly what is missing or wrong, so the assistant can fix it,

    """


def build_review_input(messages) -> str:
    question, evidence = "", []

    for message in reversed(messages[:-1]):
        if isinstance(message, HumanMessage):
            question = message.text
            break
        if isinstance(message, ToolMessage):
            evidence.append(f"[{message.name}] {message.text}")
    draft = messages[-1].text
    if evidence: 
        evidence_text = "\n\n".join(reversed(evidence))
    else:
        evidence_text = "No tools were used"
    return f"USER QUESTION:\n{question}\n\nEVIDENCE FROM TOOLS:\n{evidence_text}\n\nDRAFT ANSWER:\n{draft}"


class AgentState(MessagesState):
    verifier_feedback: str
    num_of_revisions: int

class Verdict(BaseModel):
    approved:bool
    issues: list[str]

   

tools = [get_recent_weather_data, search_knowledge_base]
assistant_model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", api_key=GEMINI_API_KEY)

verifier_model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", api_key=GEMINI_API_KEY).with_structured_output(Verdict)

assistant_model = assistant_model.bind_tools(tools)

async def assistant(state: AgentState):
    messages = [SystemMessage(assistant_system_message)] + state["messages"]
    if state.get("verifier_feedback"):
        messages.append(HumanMessage(
            f"[Reviewer feedback on your previous draft] {state['verifier_feedback']}. "
            "Fix these issues, using your tools if needed."
        ))
    response = await assistant_model.ainvoke(messages)
    if response.tool_calls:
        logger.info("Assistant → tools: %s", [(c["name"], c["args"]) for c in response.tool_calls])
    else:
        logger.info("Assistant draft: %s", response.text[:300])
    return {"messages": [response]}

async def verifier(state: AgentState):
    if state["num_of_revisions"] >= MAX_REVISIONS:
        return {"verifier_feedback": ""}  

    draft = state["messages"][-1]
    verdict = await verifier_model.ainvoke([
    SystemMessage(verifier_system_message),
    HumanMessage(build_review_input(state["messages"])),
    ])
    logger.info("Verifier approved=%s issues=%s", verdict.approved, verdict.issues)
    if verdict.approved:
        return {"verifier_feedback": ""}

    return {
        "messages": [RemoveMessage(id=draft.id)],   
        "verifier_feedback": "; ".join(verdict.issues),
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
    builder.add_conditional_edges("assistant", route_after_assistant)
    builder.add_edge("tools", "assistant")
    builder.add_conditional_edges("verifier", route_after_verifier)

    graph = builder.compile(checkpointer=InMemorySaver())

    return graph