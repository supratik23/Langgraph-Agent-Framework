from services.azure_ai_search_service import AzureAISearchClient
from fastmcp import FastMCP
import json

mcp = FastMCP("Azure AI Search Tool")

@mcp.tool()
def fetch_azure_ai_search_documents(input_data: str) -> str:
    """
    Tool to fetch relevant documents from Azure AI Search based on the organization name and ID.
    Input should be a JSON string with the following fields:
    - org_name (str): The organization name to search for in Azure AI Search.
    - org_id (str): The organization ID to search for in Azure AI Search.
    - query (str, optional): The user's question. When provided, the tool returns a compact, question-focused context.
    """
    try:
        try:
            # Parse the JSON input
            data = json.loads(input_data)
            org_name = data.get("org_name")
            org_id = data.get("org_id")
            query = data.get("query") or data.get("question") or "*"
            
            # Validate required fields
            if not org_name or not org_id:
                return "Error: Missing required fields 'org_name' or 'org_id' in input data"
    
        except json.JSONDecodeError:
            return "Error: Invalid JSON input. Please provide a valid JSON string with 'org_name' and 'org_id'."
        except Exception as e:
            return f"Error parsing input: {str(e)}"
        
        with AzureAISearchClient(organization_name=org_name, organization_id=org_id) as search_client:
            results = search_client.query_data_from_index(query)
            
            if not results:
                return "No relevant documents found in Azure AI Search."
            else:   
                return results
    except Exception as e:
        return f"Error fetching documents from Azure AI Search: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
