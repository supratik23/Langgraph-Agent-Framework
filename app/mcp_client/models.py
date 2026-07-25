from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class AgentRequest(BaseModel):
    """Agent Request Model"""
    query: str | None
    session_id: str
    user_id: str
    organization_id: str
    organization_name: str

class AgentResponse(BaseModel):
    """Agent Response Model"""
    response: str
    token_usage: str | None = None


class AgentState(TypedDict):
    """Agent State"""
    messages: Annotated[list[BaseMessage], add_messages]
    organization_id: str | None = None
    session_id: str | None = None
    organization_name: str | None = None
    user_id: str | None = None
