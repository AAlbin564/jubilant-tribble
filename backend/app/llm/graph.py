
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition

from app.llm.tools import get_recent_weather_data, search_knowledge_base
from app.config import GEMINI_API_KEY

system_message = "You are a helpful assistant with the goal of helping users with knowledge of mushrooms."

tools = [get_recent_weather_data, search_knowledge_base]


model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", api_key=GEMINI_API_KEY)

model = model.bind_tools(tools)

async def assistant(state: MessagesState):
    messages = [SystemMessage(system_message)] + state["messages"]
    response = await model.ainvoke(messages)
    return {"messages": [response]}

def build_lc_graph() -> CompiledStateGraph:

    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")

    graph = builder.compile(checkpointer=InMemorySaver())

    return graph