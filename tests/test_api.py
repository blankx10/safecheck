import pytest

from app import create_app
from extensions import db
from models import ChecklistItem, QuizScenario, ScamCheck
from routes import password as password_routes
from seeds.checklist_items import CHECKLIST_ITEMS
from seeds.quiz_scenarios import QUIZ_SCENARIOS


@pytest.fixture
def client(tmp_path):
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test"
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(tmp_path / "test.db").replace("\\", "/")
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        RATELIMIT_ENABLED = False
        RATELIMIT_STORAGE_URI = "memory://"
        MAX_SCAM_TEXT_LENGTH = 5000
        MAX_FEEDBACK_LENGTH = 500

    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        for item in CHECKLIST_ITEMS:
            db.session.add(ChecklistItem(**item))
        for item in QUIZ_SCENARIOS:
            db.session.add(QuizScenario(**item))
        db.session.commit()
        yield app.test_client()


def test_scam_check_api_and_no_plaintext(client):
    raw = "立即转账验证码冻结账户加微信"
    response = client.post(
        "/api/scam-check",
        json={"text": raw, "session_id": "session-test-1"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "risk_score" in data
    assert data["risk_level"] in ("低", "中", "高")
    row = ScamCheck.query.first()
    assert row is not None
    assert raw not in (row.text_hash or "")
    assert len(row.text_hash) == 64


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_checklist_api(client):
    response = client.get("/api/checklist?session_id=session-test-1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["progress"]["total"] == 25
    item_id = data["categories"][0]["items"][0]["id"]
    toggle = client.post(
        "/api/checklist/toggle",
        json={"session_id": "session-test-1", "item_id": item_id, "completed": True},
    )
    assert toggle.status_code == 200
    again = client.get("/api/checklist?session_id=session-test-1").get_json()
    assert again["progress"]["completed"] == 1


def test_quiz_api(client):
    response = client.get("/api/quiz")
    assert response.status_code == 200
    data = response.get_json()
    first = data["questions"][0]
    assert "correct_index" not in first
    assert "explanation" not in first
    answer = client.post(
        "/api/quiz/answer",
        json={"session_id": "session-test-1", "scenario_id": first["id"], "chosen_index": 0},
    )
    assert answer.status_code == 200
    body = answer.get_json()
    assert "is_correct" in body
    assert "correct_index" in body
    assert "explanation" in body


def test_stats_api(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.get_json()
    assert "scam_check_count" in data
    assert "session_id" not in data
    assert "text_hash" not in data


def test_hibp_proxy(client, monkeypatch):
    calls = []

    class FakeResponse:
        text = "00112233445566778899AABBCCDDEEFF0011:3\r\n"

        def raise_for_status(self):
            return None

    def fake_get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return FakeResponse()

    monkeypatch.setattr(password_routes.requests, "get", fake_get)
    response = client.get("/api/hibp/abc12")

    assert response.status_code == 200
    assert response.text.startswith("00112233445566778899AABBCCDDEEFF0011:3")
    assert response.content_type == "text/plain"
    assert calls[0][0] == "https://api.pwnedpasswords.com/range/ABC12"
    assert calls[0][1] == {"Add-Padding": "true", "User-Agent": "SafeCheck/1.0"}
    assert calls[0][2] == 10

    invalid = client.get("/api/hibp/not-a-hash")
    assert invalid.status_code == 400
    assert invalid.get_json() == {"error": "invalid prefix"}


def test_hibp_proxy_upstream_failure_is_sanitized(client, monkeypatch, caplog):
    def fake_get(url, headers, timeout):
        raise password_routes.requests.Timeout("upstream timeout")

    monkeypatch.setattr(password_routes.requests, "get", fake_get)
    response = client.get("/api/hibp/abc12")

    assert response.status_code == 502
    assert response.get_json() == {"error": "upstream failed"}
    assert "Timeout" in caplog.text
    assert "ABC12" not in caplog.text
