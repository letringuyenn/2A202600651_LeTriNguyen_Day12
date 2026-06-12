# Day 12 Codelab Solutions

Student: Le Tri Nguyen  
Student ID: 2A202600651

## Part 1: Localhost vs Production

### Exercise 1.1 - Development anti-patterns

1. Secrets and configuration are hardcoded.
2. The port and debug mode are fixed in source code.
3. There is no liveness or readiness endpoint.
4. Logs are unstructured `print()` output.
5. The process does not document graceful SIGTERM shutdown.

### Exercise 1.3 - Develop vs production

| Feature | Develop | Production | Why it matters |
|---|---|---|---|
| Configuration | Hardcoded defaults | Environment variables | One image runs in local, staging, and cloud |
| Secrets | Stored in code | Injected at runtime | Prevents credential leaks |
| Health | Missing | `/health` and `/ready` | Platforms can manage traffic and restarts |
| Logging | Plain text | Structured JSON events | Cloud logs can be searched |
| Shutdown | Abrupt | Lifespan cleanup on SIGTERM | Connections close cleanly |

## Part 2: Docker

### Exercise 2.1 - Dockerfile

1. Base image: `python:3.11-slim`.
2. Working directory: `/app`.
3. `requirements.txt` is copied first to preserve the dependency cache.
4. `CMD` is a replaceable default command; `ENTRYPOINT` fixes the executable.

### Exercise 2.3 - Multi-stage build

The builder installs packages and compilation tools. The runtime stage copies
only installed packages and application files. The final image is below 500 MB
and runs as the non-root `agent` user.

### Exercise 2.4 - Compose architecture

```text
Client -> FastAPI Helpdesk Agent :8000 -> Redis :6379
```

Redis stores conversation history, rate-limit windows, and monthly spend.

## Part 3: Cloud Deployment

- Railway uses `06-lab-complete/railway.toml` and the Dockerfile.
- Render uses `06-lab-complete/render.yaml`.
- The server binds to `0.0.0.0` and reads the platform `PORT`.
- Public URL: `TODO - fill after deployment`.

## Part 4: API Security

### Authentication

`POST /ask` requires `X-API-Key`. Missing or invalid credentials return `401`.
The secret comes from `AGENT_API_KEY`, never source code.

### Rate limiting

The API uses a Redis sorted-set sliding window with a default limit of 10
requests per minute per `user_id`. Exceeding it returns `429`.

### Cost guard

Estimated cost is accumulated in Redis per user and month. The default budget
is `$10/month`; exceeding it returns `402`.

## Part 5: Scaling and Reliability

- `/health` proves the process is alive.
- `/ready` reports startup readiness and Redis connectivity.
- Uvicorn handles SIGTERM and triggers lifespan cleanup.
- Conversation state lives in Redis, allowing multiple API replicas.
- Docker Compose verifies the agent and Redis as separate services.

## Project Assignment

The generic mock was replaced by the **CS + IT Helpdesk Supervisor-Worker Agent
from VinUni Day 9**.

Productionized workflow:

1. Supervisor classifies the question.
2. Retrieval worker selects internal knowledge.
3. Policy worker handles refund and access exceptions.
4. Human-review route flags unknown high-risk errors.
5. Synthesis returns answer, sources, confidence, workers, and trace ID.

Verified before submission:

- Docker Compose agent and Redis: healthy
- `/health`: `200`
- `/ready`: `200`
- `/ask` with key: `200`
- `/ask` without key: `401`
- Production checker: `20/20`
