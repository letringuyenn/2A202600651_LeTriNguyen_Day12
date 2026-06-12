# Deployment Information

## Public URL
_Fill this in after deploying to Railway or Render._

## Platform
Railway recommended for the fastest path, or Render if you prefer Blueprint-style deployment.

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
uvicorn app.main:app --host 0.0.0.0 --port 8000
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
docker-compose up --build
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
1. Install Railway CLI.
2. Login.
3. `railway init`
4. Set variables.
5. `railway up`
6. Get the public URL with `railway domain`

### Render
1. Push the repo to GitHub.
2. Create a new Blueprint service.
3. Let Render read `render.yaml`.
4. Set secrets in the dashboard.
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

