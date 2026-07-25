from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    ComplexField,
    CorsOptions,
    SearchIndex,
    ScoringProfile,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
)
from azure.core.credentials import AzureKeyCredential
from config import settings
import json
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureAISearchClient:
    '''
    Helper class to help with general functionalities with Azure AI Search like creating or updating index and uploading documents.
    '''
    def __init__(self, organization_name):

        self.search_service_name = settings.AZURE_SEARCH_SERVICE_NAME
        if not self.search_service_name:
            raise ValueError("AZURE_SEARCH_SERVICE_NAME environment variable not set.")

        self.api_key = settings.AZURE_SEARCH_API_KEY
        if not self.api_key:
            raise ValueError("AZURE_SEARCH_API_KEY environment variable not set.")

        self.organization_name = organization_name
        if not self.organization_name:
            raise ValueError("Organization name cannot be empty. Please provide a valid organization name.")

        self.search_endpoint = f"https://{self.search_service_name}.search.windows.net"

        self.index_name = f"{self.organization_name.lower().replace('.', ' ').replace(' ', '-').replace('--', '-')}-index"
        if not self.index_name:
            raise ValueError("Index name cannot be empty. Please provide a valid organization name.")


    def create_or_update_index(self):

        # Define the index schema
        index = SearchIndex(            
            name=f"{self.index_name}",
            fields=[
                SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True, sortable=True, facetable=True, searchable=True, retrievable=True),
                SearchableField(name="organization_name", type=SearchFieldDataType.String, filterable=True, sortable=True, facetable=True, retrievable=True),
                SearchableField(name="organization_owner", type=SearchFieldDataType.String, filterable=True, sortable=True, facetable=True, retrievable=True),
                SearchableField(name="organization_business_address_pincode", type=SearchFieldDataType.String, facetable=True, retrievable=True),
                SearchableField(name="organization_contact_number", type=SearchFieldDataType.String, filterable=True, sortable=True, facetable=True, retrievable=True),
                SearchableField(name="organization_total_members", type=SearchFieldDataType.Int32, retrievable=True, searchable=True, filterable=True, sortable=True, facetable=True),
                ComplexField(
                    name="organization_members", 
                    fields=[
                        SimpleField(name="member_name", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="user_role", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="user_phone", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="user_address", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="email", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                    ],
                    collection=True
                ),
                # New: Sites with nested members
                ComplexField(
                    name="sites",
                    fields=[
                        SimpleField(name="site_name", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="site_area", type=SearchFieldDataType.Int32, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="uom", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="address", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="city", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="pincode", type=SearchFieldDataType.Int32, searchable=True, retrievable=True),
                        SimpleField(name="state", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="latitude", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="longitude", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="constructionStatus", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="local_admin_body_name", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="local_admin_body_type", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="site_category", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        SimpleField(name="start_date", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                        ComplexField(
                            name="site_members",
                            fields=[
                                SimpleField(name="member_name", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                                SimpleField(name="joined_as", type=SearchFieldDataType.String, filterable=True, searchable=True, retrievable=True),
                                SimpleField(name="is_admin", type=SearchFieldDataType.Boolean, filterable=True, searchable=True, retrievable=True),
                                SimpleField(name="edit_all", type=SearchFieldDataType.Boolean, filterable=True, searchable=True, retrievable=True),
                                SimpleField(name="view_all", type=SearchFieldDataType.Boolean, filterable=True, searchable=True, retrievable=True),
                            ],
                            collection=True
                        )
                    ],
                    collection=True
                )
            ],
            scoring_profiles=[],
            cors_options=CorsOptions(allowed_origins=["*"])
        )

        # delete index at first if exists
        try:
            self.search_index_client.delete_index(self.index_name)
            logger.info(f"Index '{self.index_name}' deleted successfully.")
        except Exception as e:
            logger.info(f"Index '{self.index_name}' does not exist or could not be deleted: {e}")

        # Create or update the index
        self.search_index_client.create_or_update_index(index)
        logger.info(f"Index '{self.index_name}' created or updated successfully.")

    def get_index(self, index_name = None):
        """
        Retrieves the specified Azure AI Search index.

        :return: The SearchIndex object if found, otherwise None.
        """
        try:
            if index_name is None:
                index_name = self.index_name
            else:
                index_name = index_name

            index = self.search_index_client.get_index(f"{index_name}")
            logger.info(f"Index '{self.index_name}' retrieved successfully.")
            return index
        except Exception as e:
            logger.info(f"Error retrieving index '{self.index_name}': {e}")
            return None

    def upload_documents(self, documents):  
        """
        Uploads documents to the specified Azure AI Search index.

        :param documents: A list of documents to upload.
        """

        result = self.search_client.upload_documents(documents=documents)
        
        if result:
            logger.info(f"Documents uploaded successfully to index '{self.index_name}'.")
        else:
            logger.info(f"Failed to upload documents to index '{self.index_name}'.")

    def filter_index_data(self, question: str, document: dict) -> str:
        """
        Extracts relevant parts of a single index document based on keywords in the question.
        """
        question_lower = question.lower()
        parts = []

        if any(word in question_lower for word in ["summarize", "summary"]):
            return json.dumps(document, indent=2)

        if "organization members" in question_lower:
            members = document.get("organization_members", [])
            parts.append("Organization Members:")
            for member in members:
                parts.append(
                    f"- {member.get('member_name')} | Role: {member.get('user_role')} | "
                    f"Phone: {member.get('user_phone')} | Address: {member.get('user_address')} | "
                    f"Email: {member.get('email')}"
                )

        if "organization" in question_lower:
            parts.append(f"Organization Name: {document.get('organization_name')}")
            parts.append(f"Owner: {document.get('organization_owner')}")
            parts.append(f"Contact Number: {document.get('organization_contact_number')}")
            parts.append(f"Total Members: {document.get('organization_total_members')}")

        if "site" in question_lower:
            sites = document.get("sites", [])
            parts.append("Sites:")
            for site in sites:
                parts.append(
                    f"- Site Name: {site.get('site_name')} | Area: {site.get('site_area')} {site.get('uom')} | "
                    f"City: {site.get('city')} | Pincode: {site.get('pincode')} | State: {site.get('state')} | "
                    f"Latitude: {site.get('latitude')} | Longitude: {site.get('longitude')} | "
                    f"Construction Status: {site.get('constructionStatus')} | "
                    f"Local Admin Body: {site.get('local_admin_body_name')} ({site.get('local_admin_body_type')}) | "
                    f"Category: {site.get('site_category')} | Start Date: {site.get('start_date')}"
                )

        if "member" in question_lower and "organization members" not in question_lower:
            # Avoid duplication if "organization members" already handled it
            members = document.get("organization_members", [])
            parts.append("Members Info:")
            for member in members:
                parts.append(
                    f"- {member.get('member_name')} | Role: {member.get('user_role')} | "
                    f"Phone: {member.get('user_phone')} | Address: {member.get('user_address')}"
                )
        

        return "\n".join(parts) if parts else "No relevant content found."


    def query_data_from_index(self, question: str) -> str:
        """
        Queries the Azure AI Search index with the provided search text. It acts as context to the Azure OpenAI service while 
        querying for answers via user prompt.
        Use this method to search for relevant documents in the index based on the user's question and get the string output 
        which should be passed as context to query_openai method of AzureOpenAIClient class.

        :param search_text: The text to search for in the index.
        :return: A list of search results.
        """
        if not question:
            raise ValueError("Search text cannot be empty. Please provide a valid search query.")
        if not self.get_index(self.index_name):
            raise ValueError(f"Index '{self.index_name}' does not exist. Please create or update the index before querying.")

        search_val = question.strip()

        results = self.search_client.search(search_text=search_val, top=10, query_type="full", search_mode="any")
        top_chunks = []
        count = 0
        for result in results:
            count += 1
            top_chunks.append(
                f"ID: {result['id']}\n"
                f"Organization Name: {result['organization_name']}\n"
                f"Organization Owner: {result['organization_owner']}\n"
                f"Organization Business Address Pincode: {result['organization_business_address_pincode']}\n"
                f"Organization Contact Number: {result['organization_contact_number']}\n"
                f"Organization Total Members: {result['organization_total_members']}\n"
                f"Organization Members: {json.dumps(result['organization_members'], indent=2)}\n"
                f"Sites: {json.dumps(result['sites'], indent=2)}\n"         
            )

        return "\n---\n".join(top_chunks) if top_chunks else "No relevant documents found in the index."

        
    def __enter__(self):
        """
        Context manager entry method to ensure the client is ready for use.
        """
        self.search_index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
        
        self.search_client = SearchClient(self.search_endpoint, self.index_name, AzureKeyCredential(self.api_key))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Context manager exit method to clean up resources.
        """
        self.search_index_client.close()
        self.search_client.close()