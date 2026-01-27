# Docker Security & Best Practices Implementation Plan

## Overview
This document outlines the implementation plan for fixing Docker and docker-compose security issues and best practices, preparing the application for Kubernetes deployment.

**Status**: STAB-155 created (Phase 1 - Non-root user)
**Team**: StatsboardBack
**Priority**: Critical (K8s preparation)

---

## Phase 1: Critical Security Fixes (URGENT - Priority 1)

### ✅ STAB-155: Add non-root user to all Python Dockerfiles
**Status**: Created
**URL**: https://linear.app/statsboard/issue/STAB-155

**Tasks**:
- [ ] Create `appuser` with UID 1000, GID 1000 in all Python Dockerfiles
- [ ] Install curl for healthchecks
- [ ] Fix ownership of /app, /tmp directories
- [ ] Update Dockerfile.prod, Dockerfile.dev, Dockerfile.test, Dockerfile.migrations
- [ ] Update WORKDIR and COPY commands to handle permissions correctly

**Testing**:
- [ ] `docker exec -it <container> whoami` returns `appuser` (not root)
- [ ] All Dockerfiles build successfully
- [ ] Application runs without permission errors
- [ ] All tests pass

---

### ⚠️ Issue 2: Pin all image versions (no more 'latest')

**Priority**: Urgent
**Files**: Dockerfile.certbot, docker-compose.test.yml, all Python and Nginx Dockerfiles

**Tasks**:
- [ ] `certbot/certbot:latest` → `certbot/certbot:v2.8.0`
- [ ] `postgres:latest` → `postgres:17.2-alpine`
- [ ] `python:3.12-slim` → `python:3.12.3-slim` (all Python Dockerfiles)
- [ ] `nginx:alpine` → `nginx:1.27.3-alpine` (all Nginx Dockerfiles)
- [ ] Document version choices in each Dockerfile

**Rationale**:
- Prevents unpredictable builds
- Enables rollbacks
- Security best practice for K8s

---

### ⚠️ Issue 3: Enable healthchecks in all Dockerfiles

**Priority**: Urgent
**Files**: Dockerfile.prod, Dockerfile.dev, Dockerfile.test, Dockerfile.migrations

**Tasks**:
- [ ] Uncomment and fix Dockerfile.prod healthcheck (use http not https)
- [ ] Add healthchecks to Dockerfile.dev
- [ ] Add healthchecks to Dockerfile.test
- [ ] Add healthchecks to Dockerfile.migrations
- [ ] Ensure curl is installed in all Python Dockerfiles

**Implementation**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:9000/health || exit 1
```

**Rationale**:
- Required for K8s readiness/liveness probes
- Enables automatic restart of unhealthy containers
- Essential for production monitoring

---

### ⚠️ Issue 4: Improve .dockerignore file

**Priority**: Urgent
**Files**: .dockerignore

**Tasks**:
- [ ] Add Git files: `.git`, `.gitignore`
- [ ] Add Python cache: `__pycache__`, `*.pyc`, `.pytest_cache`, `.ruff_cache`
- [ ] Add environment files: `.env*` (except .env.example)
- [ ] Add documentation: `*.md`, `docs/`
- [ ] Add tests: `tests/`, `.coverage`, `coverage/`
- [ ] Add development tools: `.vscode/`, `.idea/`, `.DS_Store`
- [ ] Add build artifacts: `*.log`, `dist/`, `build/`, `*.egg-info/`

**Benefits**:
- Faster builds
- Smaller images
- Prevents sensitive data in images

---

## Phase 2: Optimizations & Best Practices (HIGH - Priority 2)

### 📋 Issue 5: Implement multi-stage builds for Python images

**Priority**: High
**Files**: Dockerfile.prod, Dockerfile.dev, Dockerfile.test

**Tasks**:
- [ ] Create multi-stage build for Dockerfile.prod
- [ ] Create multi-stage build for Dockerfile.dev
- [ ] Create multi-stage build for Dockerfile.test
- [ ] Build stage: Install all dependencies
- [ ] Production stage: Copy only runtime dependencies
- [ ] Copy application code from build stage

**Expected Results**:
- Dockerfile.prod: ~300MB → ~180MB (40% reduction)
- Faster builds and deployments
- Smaller attack surface

---

### 📋 Issue 6: Optimize layer caching in Dockerfiles

**Priority**: High
**Files**: Dockerfile.prod, Dockerfile.dev, Dockerfile.test, Dockerfile.migrations

**Tasks**:
- [ ] Reorder COPY commands (deps first, source last)
- [ ] Copy `pyproject.toml` and `poetry.lock` before source code
- [ ] Install dependencies before copying source

**Optimized Order**:
```dockerfile
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev --no-interaction --no-ansi
COPY src /app/src
```

**Benefits**:
- Faster rebuilds
- Better CI/CD performance
- Reduced bandwidth usage

---

### 📋 Issue 7: Remove poetry-cache from production

**Priority**: High
**Files**: docker-compose.prod.yml

**Tasks**:
- [ ] Remove `poetry-cache` volume definition
- [ ] Remove `- poetry-cache:/root/.cache/pypoetry` from statsboards-backend service
- [ ] Verify docker-compose.prod.yml works without volume

**Rationale**:
- Prevents cache poisoning attacks
- Reduces complexity
- Docker's build cache is sufficient

---

### 📋 Issue 8: Add resource limits to docker-compose.prod.yml

**Priority**: High
**Files**: docker-compose.prod.yml

**Tasks**:
- [ ] Add resource requests and limits to statsboards-backend service
- [ ] Add resource requests and limits to nginx-ssl service
- [ ] Add resource requests and limits to nginx-static service
- [ ] Add resource requests and limits to certbot service

**Implementation**:
```yaml
services:
  statsboards-backend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

**Rationale**:
- Prevents pod exhaustion
- Enables horizontal autoscaling
- K8s best practice

---

## Phase 3: Enhanced Security (MEDIUM - Priority 3)

### 📋 Issue 9: Fix certbot script security issues

**Priority**: Medium
**Files**: certbot-entrypoint.sh

**Tasks**:
- [ ] Remove `set -x` (verbose mode)
- [ ] Add certificate validation after generation
- [ ] Add proper error handling and logging
- [ ] Add timeout for certificate renewal
- [ ] Make email and domains configurable

**Key Improvements**:
- No sensitive data in logs
- Certificate validation
- Configurable parameters
- Better error handling

---

### 📋 Issue 10: Add security options to docker-compose.prod.yml

**Priority**: Medium
**Files**: docker-compose.prod.yml

**Tasks**:
- [ ] Add `read_only: true` to app container
- [ ] Add `tmpfs` mounts for /tmp and /run
- [ ] Add `cap_drop: ["ALL"]` for nginx containers
- [ ] Add `security_opt: ["no-new-privileges:true"]`

**Implementation**:
```yaml
services:
  statsboards-backend:
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
      - /var/tmp:noexec,nosuid,size=50m
    security_opt:
      - no-new-privileges:true
```

**Benefits**:
- Prevents container filesystem modification
- Limits impact of compromise
- CIS Docker Benchmark compliance

---

### 📋 Issue 11: Remove .env file mounting in production

**Priority**: Medium
**Files**: docker-compose.prod.yml

**Tasks**:
- [ ] Remove `env_file: - .env.prod` from docker-compose.prod.yml
- [ ] Replace with explicit environment variables
- [ ] Document required environment variables
- [ ] Update deployment documentation

**Rationale**:
- No risk of committing secrets
- Better for K8s (env vars or secrets)
- Encourages proper secrets management

---

## Implementation Order

1. **Phase 1** (All 4 items are critical for K8s readiness)
2. **Phase 2** (Optimizations make deployment faster and more secure)
3. **Phase 3** (Optional but recommended for production security)

---

## Testing Checklist

After each issue is completed:

- [ ] All Dockerfiles build successfully
- [ ] `docker-compose -f docker-compose.dev.yml up` works
- [ ] `docker-compose -f docker-compose.test.yml up` works
- [ ] `docker-compose -f docker-compose.prod.yml build` works
- [ ] All healthchecks respond
- [ ] No container runs as root (`docker exec -it <container> whoami`)
- [ ] All tests pass locally
- [ ] Images use pinned versions only

---

## Files Summary

**Phase 1**:
- Dockerfile.prod
- Dockerfile.dev
- Dockerfile.test
- Dockerfile.migrations
- Dockerfile.certbot
- docker-compose.test.yml
- .dockerignore

**Phase 2**:
- Dockerfile.prod (multi-stage)
- Dockerfile.dev (multi-stage)
- Dockerfile.test (multi-stage)
- docker-compose.prod.yml (remove poetry-cache, add resource limits)

**Phase 3**:
- certbot-entrypoint.sh
- docker-compose.prod.yml (security options, remove env_file)

---

## Next Steps

1. Complete STAB-155 (Phase 1, Issue 1) - **Currently in progress**
2. Create remaining 10 Linear issues when limit resets
3. Implement Phase 1 fixes (all 4 issues)
4. Implement Phase 2 optimizations (all 4 issues)
5. Implement Phase 3 security hardening (all 3 issues)
6. End-to-end testing

---

## Notes

- **Note**: STAB-155 was successfully created before hitting Linear's issue creation limit
- **Note**: This document serves as a comprehensive plan for all 11 issues
- **Note**: Create Linear issues when limit resets to track progress
- **Note**: All commits must be by linroot with email nevalions@gmail.com
