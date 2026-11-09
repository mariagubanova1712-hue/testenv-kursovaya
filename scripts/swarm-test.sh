#!/bin/bash
# Запуск автотестов против среды, развёрнутой в Swarm.
# Контейнер с тестами подключается к overlay-сетям стека.
set -e
docker run --rm --name testenv-swarm-tests \
  --network testenv_frontend \
  -e BASE_URL=http://nginx -e MAILPIT_URL=http://mailpit:8025 \
  testenv/tests:1.0 sh -c "pytest -v"
