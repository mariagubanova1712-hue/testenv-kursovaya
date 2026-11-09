FROM python:3.12-slim
WORKDIR /tests
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --retries 10 -r requirements.txt
COPY --chmod=644 test_api.py .
# -v подробный вывод, --junitxml отчёт для CI
CMD ["pytest", "-v", "--junitxml=/tests/report/junit.xml"]
