"""Интеграционные тесты тестовой среды.

Тесты запускаются в отдельном контейнере tests и обращаются к другим
контейнерам по сети Docker: к приложению через nginx и к Mailpit.
"""
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.getenv("BASE_URL", "http://nginx")
MAILPIT_URL = os.getenv("MAILPIT_URL", "http://mailpit:8025")


@pytest.fixture(scope="session", autouse=True)
def wait_for_app():
    """Ждём, пока среда поднимется (до 60 секунд)."""
    for _ in range(30):
        try:
            if requests.get(f"{BASE_URL}/health", timeout=2).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    pytest.fail("приложение не ответило за 60 секунд")


def test_health_all_services_ok():
    r = requests.get(f"{BASE_URL}/health")
    body = r.json()
    assert r.status_code == 200
    assert body["db"] == "ok" and body["redis"] == "ok"


def test_seed_data_loaded():
    r = requests.get(f"{BASE_URL}/api/bugs")
    assert r.status_code == 200
    assert len(r.json()) >= 5  # тестовые данные из init.sql


def test_main_page_opens():
    r = requests.get(BASE_URL)
    assert r.status_code == 200
    assert "BugBoard" in r.text


def test_create_get_update_delete_bug():
    title = f"Автотест {uuid.uuid4().hex[:6]}"
    r = requests.post(f"{BASE_URL}/api/bugs", json={"title": title, "severity": "high"})
    assert r.status_code == 201
    bug = r.json()
    assert bug["status"] == "open"

    r = requests.get(f"{BASE_URL}/api/bugs/{bug['id']}")
    assert r.json()["title"] == title

    r = requests.patch(f"{BASE_URL}/api/bugs/{bug['id']}", json={"status": "closed"})
    assert r.json()["status"] == "closed"

    assert requests.delete(f"{BASE_URL}/api/bugs/{bug['id']}").status_code == 204
    assert requests.get(f"{BASE_URL}/api/bugs/{bug['id']}").status_code == 404


def test_validation_error():
    r = requests.post(f"{BASE_URL}/api/bugs", json={"title": "", "severity": "urgent"})
    assert r.status_code == 400
    assert len(r.json()["errors"]) == 2


def test_stats_cached_in_redis():
    requests.post(f"{BASE_URL}/api/bugs", json={"title": "Сброс кэша"})
    first = requests.get(f"{BASE_URL}/api/stats").json()
    second = requests.get(f"{BASE_URL}/api/stats").json()
    assert first["cached"] is False
    assert second["cached"] is True
    assert first["data"] == second["data"]


def test_email_goes_to_mailpit():
    title = f"Проверка почты {uuid.uuid4().hex[:6]}"
    r = requests.post(f"{BASE_URL}/api/bugs", json={"title": title})
    assert r.json()["email_sent"] is True
    time.sleep(1)
    messages = requests.get(f"{MAILPIT_URL}/api/v1/messages").json()["messages"]
    assert any(title in m["Subject"] for m in messages)
