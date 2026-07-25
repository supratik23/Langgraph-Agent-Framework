
from langchain_openai import AzureChatOpenAI
from config import settings
from openai import AzureOpenAI
from typing import List, Dict, Optional
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_openai_llm():
    """Get the Azure Foundry OpenAI LLM instance. Function based implementation."""
    return AzureChatOpenAI(
                        openai_api_key=settings.OPENAI_API_KEY,
                        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                        api_version=settings.AZURE_OPENAI_API_VERSION,
                        model_name=settings.AZURE_OPENAI_MODEL,
                        temperature=0.3,
                        max_tokens=700,
                    )

class AzureOpenAIClient:

    """
    Helper class to interact with Azure OpenAI services. Class based implementation with formatted prompts.
    This class provides methods to query the OpenAI service and retrieve the response with customized prompts and contexts.
    """
    def __init__(self):
        self.openai_endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.openai_api_key = settings.OPENAI_API_KEY
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT
        if not self.openai_endpoint or not self.openai_api_key or not self.deployment_name:
            raise ValueError("Azure OpenAI endpoint or API key is not set in environment variables.")

    def format_prompt_for_query(self, context: str, question: str) -> List[Dict[str, str]]:
        """
        Formats the prompt with the provided context aand user prompt.

        :param context: Optional context to be included in the prompt.
        :param question: The question to be asked.
        :return: Formatted prompt string.
        """
        return [
            {
                "role": "system",
                "content": (
                    r"""
                    You are an assistant for the organization with an ability to give deterministic answers. 
                    Your task is to answer the question based on the data provided in the context.
                    You have the data from Azure AI Search index of an organization, 
                    so whenever you are asked to show information from the data, your response should show only the information 
                    that is asked regarding that particular organization in a polite way. Do not fabricate or invent information.
                    For count questions, use the explicit numeric fields in the context such as `count`, `matching_items`,
                    `total_items`, and organization total fields. Never infer a count by counting `sample_items`, because
                    those are previews and may be truncated.
                    """
                )
            },
            {
                "role": "system",
                "content": f"Context: {context}"
            },
            {
                "role": "user",
                "content": f"{question}"
            }
        ]

    def format_prompt_for_summarization_of_whole_json_document(self, data: str, query: str) -> List[Dict[str, str]]:
        """
        Formats the prompt with the provided organization json data that is uploaded to azure ai search index.

        :param data: The organization json data that is uploaded to azure ai search index.
        :param query: The query to ask openai service to summarize the whole json document.
        :return: Formatted prompt string.
        """
        return [
            {
                "role": "system",
                "content": (
                    r"""
                    You are a organization level assistant whose task is to summarize information from JSON data supplied to you.
                    Highlight Key information in detail like Organization and its address, contact, total members, 
                    Organization Members with their role, address, email, 
                    Sites with name, area, address, city, pincode, state, latitude, longitude,
                    construction status, local admin body name, local admin body type, site category, start date,
                    and Site Members with their name, role, phone, address, email
                    involved from the JSON data and provide a concise summary.
                    Ensure your answer should not have false positives.
                    Do not make or invent information.
                    If the JSON data is empty, respond with "No data available for summarization."

                    JSON STRUCTURE:
                    {
                        "organization_name": "Organization Name",
                        "organization_owner": "Owner Name",
                        "organization_business_address_pincode": "Pincode",
                        "organization_contact_number": "Contact Number",
                        "organization_total_members": count,
                        "organization_members": [
                            {
                                "member_name": "Member Name",
                                "user_role": "Role",
                                "user_phone": "Phone Number",
                                "user_address": "Address",
                                "email": "Email"
                            }
                        ],
                        "sites": [
                            {
                                "site_name": "Site Name",
                                "site_area": 1000,
                                "uom": "sqft",
                                "address": "Site Address",
                                "city": "City Name",
                                "pincode": 123456,
                                "state": "State Name",
                                "latitude": 12.345678,
                                "longitude": 98.765432,
                                "constructionStatus": "In Progress",
                                "local_admin_body_name": "Local Admin Body Name",
                                "local_admin_body_type": "Type of Local Admin Body",
                                "site_category": "Category of Site",
                                "start_date": "2023-01-01T00:00:00Z",
                                "site_members": [
                                    {
                                        "member_name": "Site Member Name",
                                        "joined_as": "Role in Site",
                                        "is_admin": true,
                                        "edit_all": true,
                                        "view_all": true
                                    }
                                ]
                            }
                        ]
                    }
                    """
                )
            },
            {
                "role": "system",
                "content": f"Context: {data}"
            },
            {
                "role": "user",
                "content": f"{query}"
            }
        ]

    def query_openai(self, query: str, context: str, temperature: float = 0.3, isForSumarization=False) -> str:
        """
        Queries the Azure OpenAI service with the provided prompt/query.

        :param query: The formatted prompt to be sent to the OpenAI service.
        :param context: Context to be included in the prompt. it is the output from ai search response.
        :param temperature: The temperature setting for the response generation.
        :param isForSumarization: Boolean flag to indicate if the query is for summarization of the whole document.
        :return: The response from the OpenAI service.
        """

        if isForSumarization:
            messages = self.format_prompt_for_summarization_of_whole_json_document(context, query)
        elif not isForSumarization:
            messages = self.format_prompt_for_query(context, query)
        else:
            raise ValueError("Invalid parameters: context must be provided for query or isForSumarization must be True.")

        return self.generate_response(messages, temperature)

    def format_prompt_for_refining_ai_search_data(self, context: str, data: str) -> List[Dict[str, str]]:
        '''
        Formatted prompt to refine the Azure AI Search data to be used with Azure OpenAI service.
        Refines and shortens the whole json data got from Azure AI Search as context from the index to be used with Azure OpenAI service
        in order to pass as lesser tokens as possible to the model and get deterministic answers.
        :param data: The user's question according to which the json data needs to be refined.
        :param context: The context data from Azure AI Search index. From query_data_from_index method of AzureAISearchClient class.
        :return: A list of dictionaries representing the formatted prompt.
        '''
        return [
            {
                "role": "system",
                "content": (
                r"""
                    You are an expert Data formatting assistant whose task is to get the correct and valid version of json data given in the context.
                    Refine, shorten and get valid json with only the information mentioned in the prompt to be used with Azure OpenAI service
                    in order to pass as lesser tokens as possible to the model and get deterministic answers.
                    Ensure that the data is valid and in the correct format as given in the attached index schema.
                    If there are Organization, Sites, organization members, site members,contacts, price, locations, addresses mentioned in the query, 
                    try to find them in the context and include them in the refined data.
                    Return valid json only with the information mentioned in the prompt without precesing and following string.
                    Only include the json in the curly braces.
                    If the context is empty, respond with "No data available for refinement.
                    Do not make or invent information. 
                    Ensure your answer should not have false positives."
                    
                    INDEX SCHEMA:
                        {
                            "id": "Unique identifier for the document",
                            "organization_name": "Name of the organization",
                            "organization_owner": "Owner of the organization",
                            "organization_business_address_pincode": "Pincode of the organization's business address",
                            "organization_contact_number": "Contact number of the organization",
                            "organization_total_members": "Total number of members in the organization",
                            "organization_members": [
                                {
                                    "member_name": "Name of the member",
                                    "user_role": "Role of the member in the organization",
                                    "user_phone": "Phone number of the member",
                                    "user_address": "Address of the member",
                                    "email": "Email address of the member"
                                }
                            ],
                            "sites": [
                                {
                                    "site_name": "Name of the site",
                                    "site_area": "Area of the site in square feet",
                                    "uom": "Unit of measurement for the site area",
                                    "address": "Address of the site",
                                    "city": "City where the site is located",
                                    "pincode": "Pincode of the site location",
                                    "state": "State where the site is located",
                                    "latitude": "Latitude coordinate of the site",
                                    "longitude": "Longitude coordinate of the site",
                                    "constructionStatus": "Current construction status of the site",
                                    "local_admin_body_name": "Name of the local administrative body",
                                    "local_admin_body_type": "Type of the local administrative body",
                                    "site_category": "Category of the site",
                                    "start_date": "Start date of the site project",
                                    "site_members": [
                                        {
                                            "member_name": "Name of the site member",
                                            "joined_as": "Role of the site member",
                                            "is_admin": "Whether the site member is an admin",
                                            "edit_all": "Whether the site member can edit all data",
                                            "view_all": "Whether the site member can view all data"
                                        }
                                    ]
                                }
                            ]
                        }
                """
                ),
            },
            {
                "role": "system",
                "content": f"Context: {context}"
            },
            {
                "role": "user",
                "content": f"{data}"
            }
        ]

    def generate_response(
        self, 
        prompt: List[Dict[str, str]], 
        temperature: float = 0.3, 
        max_retries: int=1,
        functions: Optional[List[Dict[str, str]]] = None,
        function_call: Optional[str] = None) -> str:
        """
        Generates a response from the Azure OpenAI service using the provided prompt.

        :param prompt: The formatted prompt to be sent to the OpenAI service.
        :param temperature: The temperature setting for the response generation.
        :param max_retries: The maximum number of retries in case of failure.
        :param functions: Optional list of functions to be used in the response.
        :param function_call: Optional function call to be used in the response.
        :return: The response from the OpenAI service.
        """
        if not self.openai_endpoint or not self.openai_api_key or not self.deployment_name:
            raise ValueError("Azure OpenAI endpoint, API key, or deployment name is not set in environment variables.")

        retries = 0
        while retries < max_retries:
            try:
                kwargs = {
                    "model": self.deployment_name,
                    "messages": prompt,
                    "temperature": temperature
                }
                if functions:
                    kwargs["functions"] = functions
                if function_call:
                    kwargs["function_call"] = function_call

                response = self.openai_client.chat.completions.create(**kwargs)
                if not response.choices or len(response.choices) == 0:
                    raise ValueError("No choices returned from OpenAI response.")

                output = response.choices[0].message
                logger.info(f"Azure OpenAi Counted tokens: {response.usage.prompt_tokens}, completion tokens: {response.usage.completion_tokens}, total tokens: {response.usage.total_tokens}")

                if hasattr(output, 'function_call'):
                    # If the response includes a function call, handle it accordingly
                    logger.info(f"Function call detected: {output.function_call}")
                    # return getattr(output.function_call, 'name', ' ').strip()
                # Return the content of the first choice's message
                if hasattr(output, 'content'):
                    return output.content.strip()
                else:
                    raise ValueError("Response does not contain 'content' in the message.")

            except Exception as e:
                logger.error(f"Error querying OpenAI: {e}")
                retries += 1
                if retries >= max_retries:
                    raise e
        logger.info("Max retries reached. Unable to get a valid response from OpenAI.")
        raise RuntimeError("Failed to get a valid response from OpenAI after maximum retries.")

    def __enter__(self):
        """
        Context manager entry method to ensure the client is ready for use.
        """
        self.openai_client = AzureOpenAI(
            api_key=self.openai_api_key,
            azure_endpoint=self.openai_endpoint,
            api_version="2025-01-01-preview"
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Context manager exit method to clean up resources.
        """
        self.openai_client.close()
