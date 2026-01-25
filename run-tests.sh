#!/bin/bash
# Run full test suite with 4 workers
# Automatically restarts test database before running tests to avoid race conditions

set -e

echo "Stopping test database..."
docker-compose -f docker-compose.test-db-only.yml stop

echo "Starting test database..."
docker-compose -f docker-compose.test-db-only.yml start

echo "Waiting for database to be ready..."
sleep 5

echo "Running tests with 4 workers..."
pytest "$@"
