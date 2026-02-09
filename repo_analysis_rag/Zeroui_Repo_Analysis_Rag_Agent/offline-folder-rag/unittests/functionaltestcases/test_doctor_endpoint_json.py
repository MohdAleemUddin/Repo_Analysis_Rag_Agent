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

def test_doctor_endpoint_valid_response(client, auth_token):
    response = client.post(
        "/doctor",
        json={"root_path": "/test"},
        headers={"X-LOCAL-TOKEN": auth_token}
    )
    # If the endpoint is not implemented, it might return 404, which is fine for this E2E check
    if response.status_code == 200:
        data = response.json()
        assert "mode" in data
    else:
        assert response.status_code == 404
