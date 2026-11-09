"""Проверка входных данных для API баг-трекера.

Вынесено в отдельный модуль, чтобы проверять эти функции модульными
тестами без запуска базы данных.
"""

SEVERITIES = ("low", "medium", "high", "critical")
STATUSES = ("open", "in_progress", "closed")


def validate_new_bug(data):
    """Возвращает список ошибок для данных нового бага (пустой - всё хорошо)."""
    errors = []
    if not isinstance(data, dict):
        return ["тело запроса должно быть JSON-объектом"]

    title = data.get("title")
    if not title or not str(title).strip():
        errors.append("поле title обязательно")
    elif len(str(title)) > 200:
        errors.append("title не длиннее 200 символов")

    severity = data.get("severity", "medium")
    if severity not in SEVERITIES:
        errors.append("severity должно быть одним из: " + ", ".join(SEVERITIES))
    return errors


def validate_status(status):
    """Проверяет новый статус бага."""
    if status not in STATUSES:
        return ["status должно быть одним из: " + ", ".join(STATUSES)]
    return []
