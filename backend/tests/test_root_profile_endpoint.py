from fastapi.testclient import TestClient

from app.main import app


def test_root_should_return_profile_label():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, str)
    assert body.startswith("hello world xhb. [")
    assert body.endswith("]")


def test_root_should_append_client_ip_from_forwarded_header():
    client = TestClient(app)
    response = client.get("/", headers={"X-Forwarded-For": "1.2.3.4, 10.0.0.1"})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, str)
    assert body.endswith("[1.2.3.4]")
