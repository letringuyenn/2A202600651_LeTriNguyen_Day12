# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded secrets in code.
2. Fixed port and config values.
3. No health check endpoint.
4. No readiness or graceful shutdown handling.
5. Debug-style local assumptions instead of environment-based config.

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcoded or local defaults | Environment variables | Easy to change per environment and avoid secret leakage |
| Health check | Often missing | `/health` endpoint | Platform can detect if the service is alive |
| Logging | Simple prints | Structured JSON logging | Easier to search, monitor, and debug in cloud logs |
| Shutdown | Abrupt stop | Graceful shutdown | Prevents dropped requests and partial work |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11-slim`
2. Working directory: `/app`
3. Copy `requirements.txt` first so Docker can cache dependency layers.
4. `CMD` can be overridden at runtime; `ENTRYPOINT` is more fixed.

### Exercise 2.3: Image size comparison
- Develop: larger single-stage image
- Production: smaller multi-stage image
- Difference: production is optimized by only copying runtime dependencies

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: _to be filled after deploy_
- Screenshot: _to be added after deploy_

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- API key auth is enforced with `X-API-Key`.
- Missing or invalid key returns `401`.
- Rate limiting is implemented with a 60-second window.

### Exercise 4.4: Cost guard implementation
- The app tracks a daily budget in memory for the lab version.
- It estimates request cost from token counts and blocks when the budget is exceeded.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- `/health` returns liveness information.
- `/ready` reports readiness.
- SIGTERM is handled for graceful shutdown.
- Stateless concerns are addressed in the lab design.
- Local testing verified the endpoints and request flow.

## Part 6: Final Project

### What is implemented in `06-lab-complete`
- FastAPI app with `/health`, `/ready`, `/ask`, and `/metrics`.
- API key authentication.
- Rate limiting.
- Cost guard.
- Structured JSON logging.
- CORS and security headers.
- Graceful shutdown handling.
- Multi-stage Dockerfile.
- Docker Compose stack.
- Railway and Render deployment configs.
- Environment-based configuration.

### Verification results
- Production readiness checker: `20/20` checks passed, `100%`.
- Local runtime test: `/health`, `/ready`, and `/ask` returned successful responses on port `8001`.
- Docker build: attempted, but Docker Hub unauthenticated pull rate limit blocked the build in this environment.

