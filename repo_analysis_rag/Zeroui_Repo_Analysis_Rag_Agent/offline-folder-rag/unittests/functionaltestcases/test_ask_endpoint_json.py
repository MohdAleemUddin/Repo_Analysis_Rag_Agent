import pytest
from fastapi.testclient import TestClient
from edge_agent.app.main import create_app
from edge_agent.app.security.token_store import get_or_create_token

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

@pytest.fixture
def auth_token():
    return get_or_create_token()

def test_ask_endpoint_valid_response(client, auth_token):
    response = client.post(
        "/ask",
        json={"query": "test query"},
        headers={"X-LOCAL-TOKEN": auth_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert "confidence" in data
    assert "answer" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)

def test_ask_endpoint_invalid_request(client, auth_token):
    response = client.post(
        "/ask",
        json={},
        headers={"X-LOCAL-TOKEN": auth_token}
    )
    assert response.status_code in [400, 422]
