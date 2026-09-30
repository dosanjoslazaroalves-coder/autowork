import os

os.environ.setdefault("AUTOWORK_TTS_ENABLED", "0")

from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "AUTOWORK"
    assert response.json()["protocol"] == 1


def test_status_reports_local_services() -> None:
    response = client.get("/api/status")
    body = response.json()
    assert response.status_code == 200
    assert body["api"] == "online"
    assert body["autowork"] == "online"
    assert body["mode"] == "local"


def test_command_uses_real_autowork_core() -> None:
    response = client.post("/api/command", json={"texto": "que horas são"})
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "sucesso"
    assert body["acao"] == "consultar_horario"
    assert body["estado"] == "SUCESSO"


def test_command_real_utf8_and_packaged_data() -> None:
    response = client.post("/api/command", json={"texto": "que horas são em Tóquio"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "sucesso"
    assert body["acao"] == "consultar_horario"
    assert "Tóquio" in body["mensagem"]
    assert body["estado"] == "SUCESSO"


def test_command_validation() -> None:
    for text in ("", "   ", "a" * 4001):
        assert client.post("/api/command", json={"texto": text}).status_code == 422


def test_status_ready_after_real_command() -> None:
    client.post("/api/command", json={"texto": "que dia é hoje"})
    status = client.get("/api/status").json()
    assert status["core"] == "online"
    assert status["ready"] is True
    assert status["state"] == "IDLE"
    assert status["last_transcript"] == "que dia é hoje"
