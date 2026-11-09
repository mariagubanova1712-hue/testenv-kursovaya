#!/bin/bash
# Удаление стека и выход из режима Swarm.
docker stack rm testenv
sleep 10
docker swarm leave --force
