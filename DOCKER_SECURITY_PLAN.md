# Docker Security & Best Practices Implementation Plan

## Overview
This document outlines the implementation plan for fixing Docker and docker-compose security issues and best practices, preparing the application for Kubernetes deployment.

**Status**: ✅ All 11 issues completed (2026-01-27)
**Team**: StatsboardBack
**Priority**: Critical (K8s preparation)

---

## Phase 1: Critical Security Fixes (URGENT - Priority 1)

### ✅ STAB-155: Add non-root user to all Python Dockerfiles
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-155
**Commit**: d0a174a

**Tasks**:
- [x] Create `appuser` with UID 1000, GID 1000 in all Python Dockerfiles
- [x] Install curl for healthchecks
- [x] Fix ownership of /app, /tmp directories
- [x] Update Dockerfile.prod, Dockerfile.dev, Dockerfile.test, Dockerfile.migrations
- [x] Update WORKDIR and COPY commands to handle permissions correctly

**Testing**:
- [x] `docker exec -it <container> whoami` returns `appuser` (not root)
- [x] All Dockerfiles build successfully
- [x] Application runs without permission errors
- [x] All tests pass

---

### ✅ STAB-158: Pin all image versions (no more 'latest')
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-158
**Commit**: 6e29acd
**Priority**: Urgent
**Files**: Dockerfile.certbot, docker-compose.test.yml, all Python and Nginx Dockerfiles

**Tasks**:
- [x] `certbot/certbot:latest` → `certbot/certbot:v2.8.0`
- [x] `postgres:latest` → `postgres:17.2-alpine`
- [x] `python:3.12-slim` → `python:3.12.3-slim` (all Python Dockerfiles)
- [x] `nginx:alpine` → `nginx:1.27.3-alpine` (all Nginx Dockerfiles)
- [x] Document version choices in each Dockerfile

**Rationale**:
- Prevents unpredictable builds
- Enables rollbacks
- Security best practice for K8s

---

### ✅ STAB-159: Enable healthchecks in all Dockerfiles
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-159
**Commit**: 37c8ff6
**Priority**: Urgent
**Files**: Dockerfile.prod, Dockerfile.dev, Dockerfile.test, Dockerfile.migrations

**Tasks**:
- [x] Uncomment and fix Dockerfile.prod healthcheck (use http not https)
- [x] Add healthchecks to Dockerfile.dev
- [x] Add healthchecks to Dockerfile.test
- [x] Add healthchecks to Dockerfile.migrations
- [x] Ensure curl is installed in all Python Dockerfiles

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

### ✅ STAB-156: Improve .dockerignore file
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-156
**Commit**: 61ba2d2
**Priority**: Urgent
**Files**: .dockerignore

**Tasks**:
- [x] Add Git files: `.git`, `.gitignore`
- [x] Add Python cache: `__pycache__`, `*.pyc`, `.pytest_cache`, `.ruff_cache`
- [x] Add environment files: `.env*` (except .env.example)
- [x] Add documentation: `*.md`, `docs/`
- [x] Add tests: `tests/`, `.coverage`, `coverage/`
- [x] Add development tools: `.vscode/`, `.idea/`, `.DS_Store`
- [x] Add build artifacts: `*.log`, `dist/`, `build/`, `*.egg-info/`

**Benefits**:
- Faster builds
- Smaller images
- Prevents sensitive data in images

---

## Phase 2: Optimizations & Best Practices (HIGH - Priority 2)

### ✅ STAB-160: Implement multi-stage builds for Python images
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-160
**Commit**: f9bc2a7
**Priority**: High
**Files**: Dockerfile.prod, Dockerfile.dev, Dockerfile.test

**Tasks**:
- [x] Create multi-stage build for Dockerfile.prod
- [x] Create multi-stage build for Dockerfile.dev
- [x] Create multi-stage build for Dockerfile.test
- [x] Build stage: Install all dependencies
- [x] Production stage: Copy only runtime dependencies
- [x] Copy application code from build stage

**Expected Results**:
- Dockerfile.prod: ~300MB → ~180MB (40% reduction)
- Faster builds and deployments
- Smaller attack surface

---

### ✅ STAB-157: Optimize layer caching in Dockerfiles
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-157
**Commit**: 42b0a24
**Priority**: High
**Files**: Dockerfile.prod, Dockerfile.dev, Dockerfile.test, Dockerfile.migrations

**Tasks**:
- [x] Reorder COPY commands (deps first, source last)
- [x] Copy `pyproject.toml` and `poetry.lock` before source code
- [x] Install dependencies before copying source

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

### ✅ STAB-163: Remove poetry-cache from production
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-163
**Commit**: bdec7e5
**Priority**: High
**Files**: docker-compose.prod.yml

**Tasks**:
- [x] Remove `poetry-cache` volume definition
- [x] Remove `- poetry-cache:/root/.cache/pypoetry` from statsboards-backend service
- [x] Verify docker-compose.prod.yml works without volume

**Rationale**:
- Prevents cache poisoning attacks
- Reduces complexity
- Docker's build cache is sufficient

---

### ✅ STAB-162: Add resource limits to docker-compose.prod.yml
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-162
**Commit**: 96e4dbe
**Priority**: High
**Files**: docker-compose.prod.yml

**Tasks**:
- [x] Add resource requests and limits to statsboards-backend service
- [x] Add resource requests and limits to nginx-ssl service
- [x] Add resource requests and limits to nginx-static service
- [x] Add resource requests and limits to certbot service

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

### ✅ STAB-161: Fix certbot script security issues
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-161
**Commit**: 68da332
**Priority**: Medium
**Files**: certbot-entrypoint.sh

**Tasks**:
- [x] Remove `set -x` (verbose mode)
- [x] Add certificate validation after generation
- [x] Add proper error handling and logging
- [x] Add timeout for certificate renewal
- [x] Make email and domains configurable

**Key Improvements**:
- No sensitive data in logs
- Certificate validation
- Configurable parameters
- Better error handling

---

### ✅ STAB-165: Add security options to docker-compose.prod.yml
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-165
**Commit**: f2e54af
**Priority**: Medium
**Files**: docker-compose.prod.yml

**Tasks**:
- [x] Add `read_only: true` to app container
- [x] Add `tmpfs` mounts for /tmp and /run
- [x] Add `cap_drop: ["ALL"]` for nginx containers
- [x] Add `security_opt: ["no-new-privileges:true"]`

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

### ✅ STAB-164: Remove .env file mounting in production
**Status**: ✅ Completed (2026-01-27)
**URL**: https://linear.app/statsboard/issue/STAB-164
**Commit**: 70e1913
**Priority**: Medium
**Files**: docker-compose.prod.yml

**Tasks**:
- [x] Remove `env_file: - .env.prod` from docker-compose.prod.yml
- [x] Replace with explicit environment variables
- [x] Document required environment variables
- [x] Update deployment documentation

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

- [x] All Dockerfiles build successfully
- [x] `docker-compose -f docker-compose.dev.yml up` works
- [x] `docker-compose -f docker-compose.test.yml up` works
- [x] `docker-compose -f docker-compose.prod.yml build` works
- [x] All healthchecks respond
- [x] No container runs as root (`docker exec -it <container> whoami`)
- [x] All tests pass locally
- [x] Images use pinned versions only

**All testing completed on 2026-01-27**

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

1. ✅ Complete STAB-155 (Phase 1, Issue 1) - **Completed on 2026-01-27**
2. ✅ Create remaining 10 Linear issues - **All created and completed**
3. ✅ Implement Phase 1 fixes (all 4 issues) - **Completed**
4. ✅ Implement Phase 2 optimizations (all 4 issues) - **Completed**
5. ✅ Implement Phase 3 security hardening (all 3 issues) - **Completed**
6. ✅ End-to-end testing - **Ready for deployment**

**All implementation steps completed. Application is ready for Kubernetes deployment.**

---

## Notes

- **Note**: STAB-155 was successfully created before hitting Linear's issue creation limit
- **Note**: This document serves as a comprehensive plan for all 11 issues
- **Note**: All Linear issues created and completed on 2026-01-27
- **Note**: All commits made by linroot with email nevalions@gmail.com
- **Completed**: All 11 issues completed and committed successfully

## Commits Summary

| Issue | Linear ID | Commit | Date | Description |
|--------|-----------|---------|-------|-------------|
| STAB-155 | https://linear.app/statsboard/issue/STAB-155 | d0a174a | 2026-01-27 | Add non-root user to all Python Dockerfiles |
| STAB-156 | https://linear.app/statsboard/issue/STAB-156 | 61ba2d2 | 2026-01-27 | Improve .dockerignore file |
| STAB-158 | https://linear.app/statsboard/issue/STAB-158 | 6e29acd | 2026-01-27 | Pin all image versions (no more 'latest') |
| STAB-159 | https://linear.app/statsboard/issue/STAB-159 | 37c8ff6 | 2026-01-27 | Enable healthchecks in all Dockerfiles |
| STAB-157 | https://linear.app/statsboard/issue/STAB-157 | 42b0a24 | 2026-01-27 | Optimize layer caching in Dockerfiles |
| STAB-160 | https://linear.app/statsboard/issue/STAB-160 | f9bc2a7 | 2026-01-27 | Implement multi-stage builds for Python images |
| STAB-162 | https://linear.app/statsboard/issue/STAB-162 | 96e4dbe | 2026-01-27 | Add resource limits to docker-compose.prod.yml |
| STAB-163 | https://linear.app/statsboard/issue/STAB-163 | bdec7e5 | 2026-01-27 | Remove poetry-cache from production |
| STAB-161 | https://linear.app/statsboard/issue/STAB-161 | 68da332 | 2026-01-27 | Fix certbot script security issues |
| STAB-164 | https://linear.app/statsboard/issue/STAB-164 | 70e1913 | 2026-01-27 | Remove .env file mounting in production |
| STAB-165 | https://linear.app/statsboard/issue/STAB-165 | f2e54af | 2026-01-27 | Add security options to docker-compose.prod.yml |
