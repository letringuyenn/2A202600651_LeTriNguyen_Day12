# Day 12 Production Helpdesk Agent

This project productionizes the **CS + IT Helpdesk Supervisor-Worker Agent**
from VinUni Day 9 (`VinUni_Day10/.../day09/lab`).

## Agent Workflow

```text
Client
  -> API key authentication
  -> Redis rate limit and monthly cost guard
  -> Supervisor
  -> Retrieval / Policy Tool / Human Review
  -> Synthesis with sources and confidence
  -> Redis conversation history
```

The agent answers questions about P1 incident SLA, refunds, access control,
login, VPN, and helpdesk troubleshooting.

## Production Features

- Environment-based configuration
- API key authentication
- Redis-backed conversation history
- Redis sliding-window rate limiting
- Monthly cost guard per user
- Health and readiness endpoints
- Structured JSON logs and trace IDs
- Graceful SIGTERM shutdown
- Multi-stage non-root Docker image
- Railway and Render configuration

## Run

```powershell
Copy-Item .env.example .env
docker-compose up --build -d
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

Ask the agent:

```powershell
$headers = @{
  "Content-Type" = "application/json"
  "X-API-Key" = "dev-key-change-me"
}
$body = @{
  "user_id" = "student-651"
  "question" = "What is the SLA for a P1 incident?"
} | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/ask -Method POST -Headers $headers -Body $body
```

Run the production checker:

```powershell
.\.venv\Scripts\python.exe check_production_ready.py
```
