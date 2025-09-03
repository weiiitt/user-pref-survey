#!/bin/bash

# Check for sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo"
    exit 1
fi

# Confirm with user before resetting database
read -p "Are you sure you want to reset the database? This will delete all data. [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Database reset cancelled."
    exit 1
fi

echo "Resetting database..."

docker compose down

truncate -s 0 dev.db  

sudo rm -rf migrations/

docker compose run --rm survey-manage db init
docker compose run --rm survey-manage db migrate
docker compose run --rm survey-manage db upgrade

echo "Database reset complete."