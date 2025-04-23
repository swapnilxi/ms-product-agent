import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_items():
    response = client.get("/items/42?q=test")
    assert response.status_code == 200
    assert response.json() == {"item_id": 42, "q": "test"}

@pytest.mark.asyncio
async def test_agent_endpoint():
    # Test with both query and company
    response = client.post(
        "/query-agent",
        json={"query": "What products?", "company": "Microsoft"}
    )
    assert response.status_code == 200
    assert "response" in response.json()

    # Test with just query
    response = client.post(
        "/query-agent",
        json={"query": "General question"}
    )
    assert response.status_code == 200