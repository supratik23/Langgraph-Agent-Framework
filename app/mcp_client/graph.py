import logging
import json
from typing import Literal
from langgraph.graph import StateGraph, START, END
from .models import AgentState
from .prompt_file import build_tool_agent_context_prompt, build_generic_agent_context_prompt, build_router_prompt
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

    # AGENT NODE 1: Define the node for AI Agent with tools. This node will handle the interaction with the LLM agent and manage tool usage.
    async def call_agent_with_tools(state: AgentState) -> dict:
        from app.main import llm_agent_with_tools

        context_message = SystemMessage(content=build_tool_agent_context_prompt(state))
        messages = [context_message, *state.get("messages", [])]
        result = await llm_agent_with_tools.ainvoke({"messages": messages})
        return {"messages": result, "next_destination": "router"}
    
    # AGENT NODE 2:Define the node for another AI Agent without tools. This node will handle the interaction with the generic LLM agent and manage responses without tool usage.
    async def call_generic_agent(state: AgentState) -> dict:
        from app.main import generic_llm_agent

        context_message = SystemMessage(content=build_generic_agent_context_prompt(state))
        messages = [context_message, *state.get("messages", [])]
        result = await generic_llm_agent.ainvoke({"messages": messages})
        return {"messages": result, "next_destination": "router"}

    # Define a function to fetch the list of available tools from the main application context. This ensures that the tool list is always up-to-date and reflects any changes made during the application's lifespan.
    def get_tools() -> list:
        from app.main import available_tools
        return available_tools

    # ROUTER NODE: This node will handle the routing of requests based on the presence of tools. It will check if tools are available and route the request to the appropriate agent node (with or without tools).
    async def router_node(state: AgentState) -> str:
        """Evaluates the input query and decides which agent should take over."""
        from app.main import generic_llm_agent

        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        prompt = build_router_prompt(last_message.content if last_message else "No query provided.")
        response = await generic_llm_agent.ainvoke({"messages": [SystemMessage(content=prompt)]})
        decision = response[0].content.strip().lower()

        if decision == "internal_agent_node":
            return {"next_destination": "internal_agent_node"}
        elif decision == "generic_agent_node":
            return {"next_destination": "generic_agent_node"}
        else:
            logger.warning(f"Unexpected routing decision: {decision}. Defaulting to 'generic_agent_node'.")
            return {"next_destination": "generic_agent_node"}

    # Define Conditional Logic for Routing: This function will be used to determine the next node in the workflow based on the availability of tools. 
    #It will return True if tools are available, allowing the workflow to proceed to the agent node with tools; 
    #otherwise, it will route to the generic agent node.
    async def route_next(state: AgentState) -> Literal["internal_agent_node", "generic_agent_node"]:
        return state["next_destination"]

    # Start building the agent state graph
    workflow = StateGraph(AgentState)

    # create nodes
    tool_node = ToolNode(get_tools(), handle_tool_errors="When creating the tool node, an error occurred: {error}. Please check the tool configuration and availability.")
    workflow.add_node("llm_agent_node", call_agent_with_tools)
    workflow.add_node("generic_agent_node", call_generic_agent)
    workflow.add_node("router", router_node)
    workflow.add_node("tools", tool_node) # keep the name of the node as "tools" to match the tools_condition function else it will not work

    # create edges
    workflow.add_edge(START, "router")

    workflow.add_conditional_edges("router", route_next, {"internal_agent_node": "llm_agent_node", "generic_agent_node": "generic_agent_node"})
    workflow.add_conditional_edges("llm_agent_node", tools_condition)
    workflow.add_edge("tools", "llm_agent_node")

    workflow.add_edge("llm_agent_node", END)
    workflow.add_edge("generic_agent_node", END)


    compiled_workflow = workflow.compile(checkpointer=checkpoint_saver)

    return compiled_workflow

async def get_agent_graph():
    """Get the agent instance"""
    global _agent
    if _agent is None:
        _agent = await agent_graph()

    return _agent


