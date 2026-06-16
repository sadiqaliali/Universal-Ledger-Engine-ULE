import pytest
from fastapi.testclient import TestClient
from ule.server.main import app

def test_server_startup():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code in [200, 404]
    print("\nServer startup test passed.")
