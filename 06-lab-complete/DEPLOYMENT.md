# Deployment Information

## Public URL
TODO - fill after Railway/Render deployment

## Platform
Railway recommended for the fastest path, or Render if you prefer Blueprint-style deployment.

## Agent Project

This service productionizes the **CS + IT Helpdesk Supervisor-Worker Agent**
from the previous VinUni Day 9 lab.

## Verified Status

- Production checker: `20/20` checks passed (`100%`)
- Docker image: built successfully with a multi-stage Dockerfile
- Docker Compose: agent and Redis containers are healthy
- `GET /health`: `200`, status `ok`
- `GET /ready`: `200`, ready `true`, Redis `connected`
- `POST /ask`: `200` with a valid `X-API-Key`
- `POST /ask`: `401` without an API key
- Conversation history: persisted in Redis and reused for follow-up questions
- Rate limit: requests 1-10 returned `200`; request 11 returned `429`

## Local Setup

### 1. Create and activate venv
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Copy environment template
```powershell
Copy-Item .env.example .env
```

### 3. Run the app locally
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Production Readiness Check

```powershell
.\.venv\Scripts\python.exe check_production_ready.py
```

Expected result:
- `20/20` checks passed
- `100%`

## Docker

### Build image
```powershell
docker build -t day12-agent .
```

### Run compose stack
```powershell
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker-compose ps
```

If Docker asks for a login or hits image pull limits, sign in to Docker Hub or retry later from a logged-in session.

## Environment Variables

Set these before deploying:

- `ENVIRONMENT=production`
- `APP_NAME=Production Helpdesk Agent`
- `APP_VERSION=2.0.0`
- `AGENT_SOURCE=VinUni Day 9 CS + IT Helpdesk Supervisor-Worker`
- `AGENT_API_KEY`
- `OPENAI_API_KEY` (server-side secret; never enter this in the browser UI)
- `OPENAI_MODEL=gpt-4o-mini`
- `MONTHLY_BUDGET_USD=10.0`
- `RATE_LIMIT_PER_MINUTE=10`
- `REDIS_URL`
- `PORT`

## Deployment Options

### Railway
1. Open Railway and create a new project from the GitHub repository.
2. Set the service root directory to `06-lab-complete`.
3. Railway will use `railway.toml` and the Dockerfile.
4. Add the environment variables listed above.
5. Add a Railway Redis service and set `REDIS_URL` to its connection URL.
6. Deploy and copy the generated public domain.

CLI alternative after installing and logging in:
```powershell
railway init
railway up
railway domain
```

### Render

Recommended Blueprint deployment:

1. Push the latest code to branch `temp`.
2. Open <https://dashboard.render.com/blueprints>.
3. Select **New Blueprint Instance**.
4. Connect the GitHub repository `2A202600651_LeTriNguyen_Day12`.
5. Render detects the root `render.yaml`; review and select **Apply**.
6. Wait until `day12-helpdesk-agent` reports **Live**.
7. Open the generated `onrender.com` URL. The demo UI is served at `/`.
8. Reveal `AGENT_API_KEY` in the service Environment page and enter it in the UI.
9. Set `OPENAI_API_KEY` in Render Environment to enable real LLM answers.

The root Blueprint targets branch `temp`, uses `rootDir: 06-lab-complete`,
and creates a free Render Key Value service for Redis-backed state.

For a manual Docker Web Service, select branch `temp`, set Root Directory
to `06-lab-complete`, set the health check path to `/health`, and add the
environment variables listed above.

## Endpoints to Test After Deploy

### Demo UI
```text
https://YOUR_PUBLIC_URL/
```

### Health
```powershell
curl https://YOUR_PUBLIC_URL/health
```

### Readiness
```powershell
curl https://YOUR_PUBLIC_URL/ready
```

### Agent Query
```powershell
curl -X POST https://YOUR_PUBLIC_URL/ask `
  -H "X-API-Key: YOUR_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"user_id\":\"student-651\",\"question\":\"What is the SLA for a P1 incident?\"}"
```

Expected response fields include:

- `answer`
- `route`
- `route_reason`
- `sources`
- `confidence`
- `workers_called`
- `trace_id`
- `history_count`

## Notes

- Do not commit a real `.env` file.
- Keep `.env.example` as the template only.
- Add screenshots of the deployed service to the repository after deployment.
