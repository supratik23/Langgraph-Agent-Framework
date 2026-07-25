import logging
import json
from langgraph.graph import StateGraph, START, END
from .models import AgentState
from langchain.messages import SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
_agent = None

# Initialize the checkpoint saver for the agent graph short term memory
checkpoint_saver = InMemorySaver()

async def agent_graph():
    """New Agent State Graph with enhanced tool handling and error management"""
    # This function is for Langgraph agent with improved features or different structure as needed.

    workflow = StateGraph(AgentState)

    async def call_model_node(state: AgentState) -> dict:
        from app.main import llm_agent_with_tools

        context_message = SystemMessage(
            content=(
                "Request context:\n"
                f"- organization_name: {state.get('organization_name')}\n"
                f"- organization_id: {state.get('organization_id')}\n"
                f"- user_id: {state.get('user_id')}\n"
                f"- session_id: {state.get('session_id')}\n"
                "Use these values whenever a tool requires them."
            )
        )
        messages = [context_message, *state.get("messages", [])]
        result = await llm_agent_with_tools.ainvoke({"messages": messages})
        return result

    def get_tools() -> list:
        from app.main import available_tools
        return available_tools

    # create nodes
    tool_node = ToolNode(get_tools(), handle_tool_errors="When creating the tool node, an error occurred: {error}. Please check the tool configuration and availability.")
    workflow.add_node("llm_agent_node", call_model_node)
    workflow.add_node("tools", tool_node) # keep the name of the node as "tools" to match the tools_condition function else it will not work

    # create edges
    workflow.add_edge(START, "llm_agent_node")
    workflow.add_conditional_edges("llm_agent_node", tools_condition)
    workflow.add_edge("tools", "llm_agent_node")
    workflow.add_edge("llm_agent_node", END)

    compiled_workflow = workflow.compile(checkpointer=checkpoint_saver)

    return compiled_workflow

async def get_agent_graph():
    """Get the agent instance"""
    global _agent
    if _agent is None:
        _agent = await agent_graph()

    return _agent


