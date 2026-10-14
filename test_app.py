from fastapi.testclient import TestClient
from app import app
import app as app_module
import pytest

#creating a temp database and linking testclient to it; instead of direct TestClient(app)
@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "db_file", tmp_path / "test.db")
    app_module.init_db()

    with TestClient(app_module.app) as test_client:
        yield test_client

#simple assert, which we run from pytest

#client = TestClient(app)

# @app.get("/"), as the return from that is same, hence we need the same here too
# .get returns a list of flat records in app.py
def test_read_main(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"Status": "OK"}

def test_get_record(client):
    response = client.get("/records")

    assert response.status_code == 200

# .post returns a nested shape o/p in app.py
def test_post_record_missing_field(client):
    response = client.post("/records", 
                           json= {
                               "prompt": "prompt",
                               "response": "response",
                               "timestamp": "time",
                               "model": "test_model",
                },
            )

    assert response.status_code == 422

#returns a nested shape o/p in app.py

def test_post_record(client):
    response = client.post("/records", 
                           json= {
                               "prompt": "prompt",
                               "response": "response",
                               "timestamp": "time",
                               "model_name": "test_model",
                },
            )

    assert response.status_code == 200
    assert response.json().keys() == {"id", "data"}

def test_delete_record(client):
    response = client.delete("/records/clear")
    sec_r = client.get("/records")

    assert response.status_code == 200
    assert response.json() == {"message": "data cleared"}

    assert sec_r.status_code == 200