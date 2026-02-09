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

def test_overview_endpoint_valid_response(client, auth_token):
    response = client.post(
        "/overview",
        json={"root_path": "/test"},
        headers={"X-LOCAL-TOKEN": auth_token}
    )
    if response.status_code == 200:
        data = response.json()
        assert "mode" in data
        assert "answer" in data
    else:
        assert response.status_code == 404
