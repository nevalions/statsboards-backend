#!/bin/bash
# Run tests with random order to detect order-dependent tests
# Automatically restarts test database, clears lock files, and waits for readiness

set -e

echo "=========================================="
echo "Running tests with random order..."
echo "=========================================="
echo "Seed will be printed for reproducibility"
echo ""
echo "If tests failed, re-run with the same seed to reproduce:"
echo "./run-tests-random.sh --random-order-seed=<SEED>"
echo ""

# Run with random order
./run-tests.sh --random-order "$@"

echo ""
echo "=========================================="
echo "Test run complete"
echo "=========================================="
