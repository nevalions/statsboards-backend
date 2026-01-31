#!/bin/bash
# Run full test suite with 4 workers
# Automatically restarts test database, clears lock files, and waits for readiness

set -e

# Default values
DB_TEST_USER="${DB_TEST_USER:-postgres}"
DB_TEST_NAME="${DB_TEST_NAME:-test_db}"

echo "=========================================="
echo "Test Suite Runner"
echo "=========================================="

echo "1/4 Stopping test database..."
docker-compose -f docker-compose.test-db-only.yml stop

echo "2/4 Cleaning up stale lock files..."
rm -f /tmp/test_db_tables_setup_*.lock
rm -f /tmp/test_db_setup_complete_*.marker

echo "3/4 Starting test database..."
docker-compose -f docker-compose.test-db-only.yml start

echo "4/4 Waiting for database to be ready..."
max_attempts=30
attempt=0

# Wait for container to be responsive
sleep 2

until docker-compose -f docker-compose.test-db-only.yml exec -T postgres_test \
    pg_isready -U "${DB_TEST_USER}" -d "${DB_TEST_NAME}" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "Error: Database failed to become ready after ${max_attempts} seconds"
        docker-compose -f docker-compose.test-db-only.yml logs postgres_test
        exit 1
    fi
    echo "  Waiting... (${attempt}/${max_attempts})"
    sleep 1
done

echo "=========================================="
echo "Database ready! Running tests..."
echo "=========================================="

pytest "$@"
