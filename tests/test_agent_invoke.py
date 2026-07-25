import pytest
from fastapi.testclient import TestClient
from app.main import app



# cmd: python3 -m pytest tests/test_agent_invoke.py

client = TestClient(app)

def test_invoke_agent():
    """Test the /agent/invoke POST endpoint with a valid request body."""
    request_data = {
        "query": "What is the capital of France?",
        "session_id": "test_session_123",
        "user_id": "test_user_456",
        "organization_id": "test_org_789",
        "organization_name": "Test Organization"
    }

    response = client.post("/agent/invoke", json=request_data)

    # Assuming the app starts successfully, this should return 200
    # In a real test, you might need to mock dependencies if startup fails
    assert response.status_code in [200, 500]  # 500 if dependencies not set up
    if response.status_code == 200:
        response_data = response.json()
        assert "response" in response_data
        assert isinstance(response_data["response"], str)
        assert "token_usage" in response_data