from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from agents.retrieval_tool import retrieve_documents
from agents.memory_tool import read_user_profile, update_user_profile
from memory.user_profile import format_profile_for_prompt
from models.claude import get_llm

TOOLS = [retrieve_documents, read_user_profile, update_user_profile]

_SYSTEM_TEMPLATE = """You are a personal AI assistant with access to the user's document knowledge base and memory.

Use the retrieve_documents tool to search for relevant information before answering questions about documents.
Use read_user_profile to recall facts about the user when relevant.
Use update_user_profile to note important new facts about the user during conversation.

User profile:
{profile}

Always ground your answers in retrieved documents when available. Be concise and direct."""


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def _build_graph():
    llm = get_llm().bind_tools(TOOLS)

    def agent_node(state: AgentState) -> AgentState:
        profile = format_profile_for_prompt()
        system = SystemMessage(content=_SYSTEM_TEMPLATE.format(profile=profile))
        response = llm.invoke([system] + state["messages"])
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


agent_graph = _build_graph()


async def run_agent(message: str, history: list[BaseMessage]) -> str:
    from langchain_core.messages import HumanMessage

    state = {"messages": history + [HumanMessage(content=message)]}
    result = await agent_graph.ainvoke(state)
    return result["messages"][-1].content
