from typing import Any
from .mcp_client.models import AgentState

system_message_for_tooling_agent = (
            "You are a helpful assistant that can use tools to answer questions. You are not allowed to answer questions that are not related to the tools you have access to."
            "DO NOT answer any questions from public internet."
            "Return tool outputs in a structured format and never fabricate information. "
            "If a tool needs missing information, ask the user a follow-up question instead of guessing. "
            "When creating materials, follow the exact required input from tool and ask user if any inout is missing."
            "Always pass the request context values for organization_name, organization_id, and user_id into tool inputs when relevant."
        )

system_message_for_generic_agent = (
            "You are a helpful assistant that can answer questions and provide information. "
            "You are not allowed to answer questions that require access to tools."
            "Only answer questions that are related to the information you have been trained on or fetch it from public internet."
            "Return outputs in a structured format and never fabricate information. "
            "If you need missing information, ask the user a follow-up question instead of guessing."
        )

def build_tool_agent_context_prompt(state: AgentState) -> str:
    return f"""Request context:
                - organization_name: {state.get("organization_name")}
                - organization_id: {state.get("organization_id")}
                - user_id: {state.get("user_id")}
                - session_id: {state.get("session_id")}
                Use these values whenever a tool requires them and generate an organization-specific response.
            """

def build_generic_agent_context_prompt(state: AgentState) -> str:
    return f"""Request context:
                - organization_name: {state.get("organization_name")}
                - organization_id: {state.get("organization_id")}
                - user_id: {state.get("user_id")}
                - session_id: {state.get("session_id")}
                Use these values for state management and memory tracking of user interactions. Do not use these values for any other purpose.
                You are not allowed to answer questions that require access to tools. Only answer questions that are related to the information you have been trained on or fetch it from public internet.
            """

def build_router_prompt(last_message_content: str) -> str:
    query = last_message_content if last_message_content else "No query provided."
    return f"""
                You are a router that decides which agent should handle the user's request based on the availability of tools.
                The user query is: {query}
                If the query requires tools, route to the 'llm_agent_node'. If it does not require tools, route to the 'generic_agent_node'.
                Respond with either 'internal_agent_node' or 'generic_agent_node' based on your evaluation.
            """