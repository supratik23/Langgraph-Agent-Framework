from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import sys

python_path = os.pathsep.join([os.path.abspath("."), os.path.abspath("app")])
python_command = sys.executable

mcp_servers_config = {
    "create_task_record": {
        "transport": "stdio",
        "command": "python3",
        "args":[os.path.abspath("app/mcp_server/taskcreate_tool.py")],
        "env": {"PYTHONPATH": python_path}
    },
    "create_material_record": {
        "transport": "stdio",
        "command": "python3",
        "args":[os.path.abspath("app/mcp_server/create_material_tool.py")],
        "env": {"PYTHONPATH": python_path}
    },
    "fetch_azure_ai_search_documents": {
        "transport": "stdio",
        "command": "python3",
        "args":[os.path.abspath("app/mcp_server/ai_search_document_tool.py")],
        "env": {"PYTHONPATH": python_path}
    },
}

multi_server_mcp_client = MultiServerMCPClient(mcp_servers_config)

