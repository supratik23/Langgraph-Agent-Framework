import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.azure_ai_search_service import AzureAISearchClient


def _client() -> AzureAISearchClient:
    return object.__new__(AzureAISearchClient)


def test_filter_index_data_returns_full_item_for_specific_work_order_query():
    client = _client()
    document = {
        "organization_id": "1",
        "organization_name": "Test Org",
        "work_orders": [
            {
                "work_order_id": "46",
                "contractor_id": "20",
                "contractor_name": "shyam",
                "site_id": "5",
                "site_name": "Site Mutation",
                "status": "UNPAID",
                "is_acknowledged": False,
                "contract_type": "LABOUR",
                "payment_structure": "LUMPSUM_CUSTOM",
                "preferred_payment_mode": "CASH",
                "start_date": None,
                "end_date": "2025-11-26",
                "total_value": 0,
                "total_paid": 0,
                "created_by": "Apratim Dutta",
                "date_of_issue": "2025-11-23",
            }
        ],
    }

    response = client.filter_index_data("show work order 46", document)
    payload = json.loads(response)

    work_orders = payload["relevant_sections"]["work_orders"]
    assert work_orders["items_returned"] == 1
    assert "end_date" in work_orders["sample_items"][0]
    assert "payment_structure" in work_orders["sample_items"][0]
    assert work_orders["sample_items"][0]["work_order_id"] == "46"


def test_filter_index_data_maps_field_name_queries_to_matching_collection():
    client = _client()
    document = {
        "organization_id": "1",
        "organization_name": "Test Org",
        "work_orders": [
            {
                "work_order_id": "46",
                "contractor_name": "shyam",
                "status": "UNPAID",
                "end_date": None,
            }
        ],
    }

    response = client.filter_index_data("show end date", document)
    payload = json.loads(response)

    work_orders = payload["relevant_sections"]["work_orders"]
    assert work_orders["requested_fields"] == ["end_date"]
    assert work_orders["sample_items"][0]["work_order_id"] == "46"
    assert "end_date" in work_orders["sample_items"][0]
    assert work_orders["sample_items"][0]["end_date"] is None
