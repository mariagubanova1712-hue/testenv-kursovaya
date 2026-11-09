#!/bin/bash
# Развёртывание тестовой среды в кластере Docker Swarm (один узел - Docker Desktop).
set -e
cd "$(dirname "$0")/.."

# переменные из .env (логин/пароль тестовой базы)
set -a; [ -f .env ] && source .env; set +a

# 1. инициализация кластера, если он ещё не создан
if [ "$(docker info --format '{{.Swarm.LocalNodeState}}')" != "active" ]; then
  echo ">>> docker swarm init"
  docker swarm init
fi

# 2. сборка своих образов
echo ">>> сборка образов"
docker compose build nginx app db
docker compose --profile test build tests

# 3. развёртывание стека
echo ">>> docker stack deploy"
docker stack deploy -c docker-stack.yml --resolve-image never testenv

echo ">>> ждём запуска сервисов..."
sleep 20
docker stack services testenv
