FROM python:3.12-slim

# не создавать .pyc и сразу выводить логи
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# приложение запускается не от root
RUN useradd --create-home appuser
# --chmod: права на файлы задаются явно и не зависят от прав на компьютере разработчика
COPY --chown=appuser:appuser --chmod=755 . .
USER appuser

EXPOSE 5000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
