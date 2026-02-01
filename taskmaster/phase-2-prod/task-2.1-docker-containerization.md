# Task 2.1: Docker Containerization

## Objective
Containerize all ODAOS components for deployment to OKE.

## Prerequisites
- Phase 1 MVP completed and tested
- Docker Desktop installed on development machine

## Tasks

### 2.1.1 Create Multi-Stage Dockerfile
- [ ] Create `docker/Dockerfile` with multi-stage build
- [ ] Base image: python:3.11-slim
- [ ] Install Oracle Instant Client in container
- [ ] Install Python dependencies
- [ ] Configure non-root user for security
- [ ] Add health check endpoint
- [ ] Optimize image size (<500MB target)

### 2.1.2 Create docker-compose.yml
- [ ] Create `docker/docker-compose.yml`
- [ ] Define mcp-servers service
- [ ] Define agent-orchestrator service
- [ ] Configure shared network
- [ ] Mount volumes for logs and config
- [ ] Configure environment variable injection

### 2.1.3 Convert MCP Servers to HTTP Mode
- [ ] Update Performance MCP Server for HTTP transport
- [ ] Update Self-Healing MCP Server for HTTP transport
- [ ] Update Cost Optimization MCP Server for HTTP transport
- [ ] Add FastAPI wrapper for REST API
- [ ] Test HTTP mode locally

### 2.1.4 Add Health Check Endpoints
- [ ] Add `/health` endpoint to each service
- [ ] Add `/ready` endpoint for Kubernetes probes
- [ ] Include database connectivity check
- [ ] Include LLM API connectivity check

### 2.1.5 Test Local Docker Deployment
- [ ] Build images: `docker-compose build`
- [ ] Run locally: `docker-compose up`
- [ ] Test all API endpoints
- [ ] Verify container-to-container communication
- [ ] Test database connectivity (SSH tunnel from host)

### 2.1.6 Create .dockerignore
- [ ] Exclude venv, __pycache__
- [ ] Exclude .env, *.pem, *.key
- [ ] Exclude logs, data directories
- [ ] Exclude test files

## Completion Criteria
- [ ] Docker images build successfully
- [ ] Containers start without errors
- [ ] All services respond to health checks
- [ ] API endpoints functional
- [ ] Image size optimized (<500MB each)

## Estimated Duration
**6-8 hours**

## Dockerfile Structure
```dockerfile
# Stage 1: Build
FROM python:3.11-slim as builder
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# ... install Oracle Instant Client
USER appuser
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
```

## Dependencies
- Phase 1 MVP completed

## Phase 1 Reuse
- All Python code reused directly
- Configuration via environment variables (already implemented)
- MCP servers just need HTTP transport wrapper
