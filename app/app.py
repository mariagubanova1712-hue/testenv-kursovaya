"""BugBoard - небольшой баг-трекер, тестируемое веб-приложение.

Приложение работает в контейнере app и обращается к другим контейнерам
тестовой среды по их именам в сети Docker:
  db      - PostgreSQL, хранение багов;
  redis   - кэш для статистики;
  mailpit - тестовый SMTP-сервер, принимает письма-уведомления.
"""
import json
import os
import smtplib
import socket
from email.message import EmailMessage

import psycopg
import redis
from flask import Flask, jsonify, render_template, request

from validators import validate_new_bug, validate_status

DB_DSN = os.getenv(
    "DATABASE_URL", "postgresql://testenv:testenv@db:5432/bugboard"
)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
SMTP_HOST = os.getenv("SMTP_HOST", "mailpit")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
STATS_TTL = int(os.getenv("STATS_CACHE_TTL", "30"))
APP_ENV = os.getenv("APP_ENV", "test")

app = Flask(__name__)
app.json.ensure_ascii = False  # кириллица в JSON без \u-кодов
cache = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


def db():
    """Новое подключение к базе на каждый запрос (для учебного проекта хватает)."""
    return psycopg.connect(DB_DSN, row_factory=psycopg.rows.dict_row)


def row_to_json(row):
    row = dict(row)
    row["created_at"] = row["created_at"].isoformat()
    return row


def notify(bug):
    """Письмо о новом баге уходит в Mailpit, а не реальным людям."""
    msg = EmailMessage()
    msg["Subject"] = f"Новый баг #{bug['id']}: {bug['title']}"
    msg["From"] = "bugboard@testenv.local"
    msg["To"] = "qa-team@testenv.local"
    msg.set_content(
        f"Заведён баг #{bug['id']}\n"
        f"Серьёзность: {bug['severity']}\n\n{bug['description'] or ''}"
    )
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as smtp:
            smtp.send_message(msg)
        return True
    except OSError as e:
        app.logger.warning("письмо не отправлено: %s", e)
        return False


@app.get("/health")
def health():
    """Проверка, что приложение видит базу и Redis. Используется в healthcheck."""
    state = {"app": "ok", "env": APP_ENV, "hostname": socket.gethostname()}
    code = 200
    try:
        with db() as conn:
            conn.execute("SELECT 1")
        state["db"] = "ok"
    except Exception as e:
        state["db"] = f"error: {e.__class__.__name__}"
        code = 503
    try:
        cache.ping()
        state["redis"] = "ok"
    except Exception as e:
        state["redis"] = f"error: {e.__class__.__name__}"
        code = 503
    return jsonify(state), code


@app.get("/")
def index():
    with db() as conn:
        bugs = conn.execute("SELECT * FROM bugs ORDER BY id DESC").fetchall()
    return render_template("index.html", bugs=bugs, host=socket.gethostname(), env=APP_ENV)


@app.get("/api/bugs")
def list_bugs():
    status = request.args.get("status")
    with db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM bugs WHERE status = %s ORDER BY id", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM bugs ORDER BY id").fetchall()
    return jsonify([row_to_json(r) for r in rows])


@app.post("/api/bugs")
def create_bug():
    data = request.get_json(silent=True)
    errors = validate_new_bug(data)
    if errors:
        return jsonify({"errors": errors}), 400
    with db() as conn:
        bug = conn.execute(
            "INSERT INTO bugs (title, description, severity) VALUES (%s, %s, %s) "
            "RETURNING *",
            (data["title"].strip(), data.get("description", ""),
             data.get("severity", "medium")),
        ).fetchone()
    cache.delete("stats")  # статистика изменилась
    bug = row_to_json(bug)
    bug["email_sent"] = notify(bug)
    return jsonify(bug), 201


@app.get("/api/bugs/<int:bug_id>")
def get_bug(bug_id):
    with db() as conn:
        bug = conn.execute("SELECT * FROM bugs WHERE id = %s", (bug_id,)).fetchone()
    if bug is None:
        return jsonify({"error": "баг не найден"}), 404
    return jsonify(row_to_json(bug))


@app.patch("/api/bugs/<int:bug_id>")
def update_status(bug_id):
    data = request.get_json(silent=True) or {}
    errors = validate_status(data.get("status"))
    if errors:
        return jsonify({"errors": errors}), 400
    with db() as conn:
        bug = conn.execute(
            "UPDATE bugs SET status = %s WHERE id = %s RETURNING *",
            (data["status"], bug_id),
        ).fetchone()
    if bug is None:
        return jsonify({"error": "баг не найден"}), 404
    cache.delete("stats")
    return jsonify(row_to_json(bug))


@app.delete("/api/bugs/<int:bug_id>")
def delete_bug(bug_id):
    with db() as conn:
        cur = conn.execute("DELETE FROM bugs WHERE id = %s", (bug_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "баг не найден"}), 404
    cache.delete("stats")
    return "", 204


@app.get("/api/stats")
def stats():
    """Количество багов по статусам. Результат кэшируется в Redis."""
    cached = cache.get("stats")
    if cached:
        return jsonify({"cached": True, "data": json.loads(cached)})
    with db() as conn:
        rows = conn.execute(
            "SELECT status, count(*) AS n FROM bugs GROUP BY status"
        ).fetchall()
    data = {r["status"]: r["n"] for r in rows}
    cache.setex("stats", STATS_TTL, json.dumps(data))
    return jsonify({"cached": False, "data": data})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
