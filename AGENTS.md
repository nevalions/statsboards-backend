# AGENTS.md

This file provides guidance for agentic coding assistants working in this repository.

## Overview

For detailed development guidelines, coding standards, and best practices, see **[DEVELOPMENT_GUIDELINES.md](./DEVELOPMENT_GUIDELINES.md)**.

This document serves as a quick reference for common operations and links to the comprehensive guidelines.

## Quick Reference

### Essential Commands

**Testing:**
```bash
# Start test database
docker-compose -f docker-compose.test-db-only.yml up -d

# Run all tests (parallel by default)
pytest

# Run tests sequentially (for debugging or full test suite)
pytest -n 0

# Run with coverage
pytest --cov=src --cov-report=html
```

**Code Quality:**
```bash
# Lint with Ruff
source venv/bin/activate && ruff check src/ tests/

# Auto-fix Ruff issues
source venv/bin/activate && ruff check --fix src/ tests/
```

**Database:**
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1
```

### Key Documents

- **[DEVELOPMENT_GUIDELINES.md](./DEVELOPMENT_GUIDELINES.md)** - Comprehensive development guide with all coding standards, patterns, and best practices
- **[SERVICE_LAYER_DECOUPLING.md](./SERVICE_LAYER_DECOUPLING.md)** - Service layer architecture and dependency injection patterns
- **[CONFIGURATION_VALIDATION.md](./CONFIGURATION_VALIDATION.md)** - Configuration settings and validation details

### Test Suite Status

All 500+ tests are passing. For detailed test information and recent fixes, see the [Test Suite Status](./DEVELOPMENT_GUIDELINES.md#test-suite-status) section in DEVELOPMENT_GUIDELINES.md.

### Search Testing Guidelines

Search functionality has been refactored to use shared `SearchPaginationMixin` for consistency. See the [Search Testing Guidelines](./DEVELOPMENT_GUIDELINES.md#search-testing-guidelines) section in DEVELOPMENT_GUIDELINES.md for details.

### Tooling and Testing

| Tool | Purpose | Command |
|------|----------|----------|
| pytest | Test runner | `pytest` |
| pytest-xdist | Parallel test execution | `pytest -n auto` |
| pytest-cov | Coverage reporting | `pytest --cov=src` |
| pytest-benchmark | Performance benchmarks | `pytest tests/test_benchmarks.py -m benchmark` |
| Hypothesis | Property-based testing | `pytest tests/test_property_based.py` |
| Ruff | Linting | `ruff check src/ tests/` |
| Alembic | Database migrations | `alembic upgrade head` |

### Test Markers

- `@pytest.mark.integration` - Tests that hit external websites or write to production folders
- `@pytest.mark.benchmark` - Performance benchmark tests
- `@pytest.mark.e2e` - End-to-end integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.property` - Property-based tests

### Important Notes

**Note:** Do not add AGENTS.md to README.md - this file is for development reference only.

**Note:** All commits must be by linroot with email nevalions@gmail.com

**Note:** When you need to search docs, use `context7` tools.

### Workflow References

See DEVELOPMENT_GUIDELINES.md for:
- Code style guidelines and naming conventions
- Service layer and router patterns
- Model patterns and relationship types
- Error handling patterns
- Database operations and relationship loading
- Search implementation guidelines
- WebSocket and real-time patterns
- Configuration validation details
