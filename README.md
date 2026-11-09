# Тестовая среда для разработки и тестирования веб-приложений

Курсовая работа по дисциплине «Настройка и администрирование сервисного программного обеспечения».
Губанова М. Д., группа ИКБО-13-25, РТУ МИРЭА.

Тема: «Настройка и администрирование управления тестовой средой для разработки и тестирования веб-приложений».

## Что это

Набор из 7 Docker-контейнеров, который за одну команду поднимает полноценную тестовую среду
для веб-приложения BugBoard (простой баг-трекер на Flask). Разработчик или тестировщик получает
на своём компьютере всё, что нужно приложению: базу с тестовыми данными, кэш, почтовый сервер
и автотесты.

| № | Контейнер | Образ | Назначение | Порт на хосте |
|---|-----------|-------|------------|---------------|
| 1 | nginx   | testenv/nginx (nginx:1.27-alpine) | обратный прокси, единая точка входа | 8080 |
| 2 | app     | testenv/app (python:3.12-slim)    | тестируемое веб-приложение Flask + Gunicorn | — |
| 3 | db      | testenv/db (postgres:16-alpine)   | PostgreSQL со схемой и тестовыми данными | — |
| 4 | redis   | redis:7-alpine                    | кэш статистики | — |
| 5 | mailpit | axllent/mailpit                   | тестовый SMTP: письма не уходят наружу | 8025 |
| 6 | adminer | adminer                           | веб-интерфейс к базе | 8081 |
| 7 | tests   | testenv/tests (python:3.12-slim)  | интеграционные автотесты pytest | — |

## Структура проекта

```
.
├── app/                 # тестируемое приложение
│   ├── app.py           # Flask: REST API /api/bugs, /api/stats, /health
│   ├── validators.py    # проверка входных данных
│   ├── templates/       # HTML-страница
│   ├── tests/           # модульные тесты
│   ├── requirements.txt
│   └── Dockerfile
├── db/                  # init.sql - схема и тестовые данные, Dockerfile
├── nginx/               # nginx.conf, Dockerfile
├── tests/               # интеграционные тесты, Dockerfile
├── scripts/             # скрипты для Docker Swarm
├── docker-compose.yml   # запуск среды на одной машине
├── docker-stack.yml     # развёртывание в кластере Docker Swarm
├── .env.example         # тестовые переменные окружения
└── .github/workflows/ci-cd.yml   # CI/CD в GitHub Actions
```

## Запуск (Docker Compose)

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
```

- приложение: http://localhost:8080
- письма: http://localhost:8025
- база (Adminer): http://localhost:8081 (сервер `db`, логин/пароль из `.env`)

Автотесты:

```bash
docker compose --profile test run --rm tests
```

Остановка с удалением данных: `docker compose --profile test down -v`

## Кластер Docker Swarm

```bash
./scripts/swarm-deploy.sh    # swarm init + сборка + docker stack deploy
docker stack services testenv
./scripts/swarm-test.sh      # автотесты против кластера
docker service scale testenv_app=5
./scripts/swarm-remove.sh    # удалить стек и выйти из swarm
```

## CI/CD

При каждом push в `main` GitHub Actions выполняет: модульные тесты → сборку всех контейнеров и
интеграционные тесты → публикацию образов в GitHub Container Registry → развёртывание стека в
Docker Swarm и smoke-тест.
