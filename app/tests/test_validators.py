"""Модульные тесты: запускаются без базы данных, первым этапом CI."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validators import validate_new_bug, validate_status  # noqa: E402


def test_correct_bug_has_no_errors():
    assert validate_new_bug({"title": "Кнопка не нажимается", "severity": "high"}) == []


def test_title_is_required():
    assert "поле title обязательно" in validate_new_bug({"title": "   "})


def test_title_too_long():
    assert validate_new_bug({"title": "x" * 201})


def test_wrong_severity():
    assert validate_new_bug({"title": "ok", "severity": "urgent"})


def test_body_must_be_object():
    assert validate_new_bug(["не", "объект"])


def test_status_values():
    assert validate_status("closed") == []
    assert validate_status("done")
