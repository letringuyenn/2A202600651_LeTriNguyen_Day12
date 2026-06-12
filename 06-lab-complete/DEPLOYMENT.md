# Deployment Information

## Public URL
TODO - fill after Railway/Render deployment

## Platform
Railway recommended for the fastest path, or Render if you prefer Blueprint-style deployment.

## Verified Status

- Production checker: `20/20` checks passed (`100%`)
- Docker image: built successfully with a multi-stage Dockerfile
- Docker Compose: agent and Redis containers are healthy
- `GET /health`: `200`, status `ok`
- `GET /ready`: `200`, ready `true`
- `POST /ask`: `200` with a valid `X-API-Key`
- `POST /ask`: `401` without an API key

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
- `APP_NAME=Production AI Agent`
- `APP_VERSION=1.0.0`
- `OPENAI_API_KEY` or leave empty to use the mock LLM
- `AGENT_API_KEY`
- `JWT_SECRET`
- `DAILY_BUDGET_USD`
- `RATE_LIMIT_PER_MINUTE`
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
1. Push the repo to GitHub.
2. Create a new Blueprint or Docker Web Service.
3. Set the root directory to `06-lab-complete`.
4. Use `render.yaml`, then verify generated secrets in the dashboard.
5. Deploy and copy the public URL.

## Endpoints to Test After Deploy

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
  -d "{\"question\":\"Hello\"}"
```

## Notes

- Do not commit a real `.env` file.
- Keep `.env.example` as the template only.
- Add screenshots of the deployed service to the repository after deployment.
