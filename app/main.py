# FastAPI application level api url setup and app lifecycle management

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .mcp_client.agent import agent_router
from .mcp_client.serverconfig import multi_server_mcp_client
from langchain.agents import create_agent
from app.services.llm_service import get_openai_llm
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

available_tools = []
llm_agent_with_tools = None

@asynccontextmanager
async def lifespan(app: FastAPI): 
    """
    Application lifespan management for startup and shutdown events. 
    Start the mcp_server tools and LLM agent on application startup, and perform any necessary cleanup on shutdown.
    """
    try:
        global available_tools, llm_agent_with_tools, generic_llm_agent

        # Fetch the list of available tools from the MCP server client
        available_tools = await multi_server_mcp_client.get_tools()

        # get the LLM model
        llm = get_openai_llm()

        # Create 2 LLM agents - one  with the available tools and other just a generic agent without tools. Both agents have different system prompts to guide their behavior.
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
        llm_agent_with_tools = create_agent(llm, available_tools, system_prompt=system_message_for_tooling_agent)
        generic_llm_agent = create_agent(llm, [], system_prompt=system_message_for_generic_agent)

        logger.info("application_starting")

        yield
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        logger.error(traceback.format_exc())
        raise e
    finally:
        logger.info("application_shutting_down")

# ----------------------------------------------------------------------------------------

app = FastAPI(
    title="Langgraph Agent API",
    description="AI Agent with FastAPI, LangGraph, and MCP. Works for B2B and B2C scenarios.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter()
app.include_router(agent_router, prefix="/agent", tags=["agent"])

@app.get("/health")
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
        }
    )

@app.get("/")
async def root():
    return {
        "message": "AI Agent API",
        "docs": "/docs",
        "version": "0.1.0",
    }
