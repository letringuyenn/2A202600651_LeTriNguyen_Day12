# Day 12 Lab - Solution

**Sinh viên:** Le Tri Nguyen<br>
**Mã sinh viên:** 2A202600651<br>
**Dự án:** Production Helpdesk Supervisor-Worker Agent<br>
**Nền tảng deploy:** Render<br>
**Public URL:** <https://day12-helpdesk-agent.onrender.com><br>
**Health check:** <https://day12-helpdesk-agent.onrender.com/health><br>
**Readiness check:** <https://day12-helpdesk-agent.onrender.com/ready>

---

## Part 1: Localhost vs Production

### Exercise 1.1: Phát hiện anti-patterns

Các vấn đề trong phiên bản development:

1. Secret và cấu hình bị hardcode trong source code.
2. Host, port và debug mode được đặt cố định.
3. Không có endpoint `/health` và `/ready`.
4. Logging dùng `print()` thay vì structured logging.
5. Không xử lý graceful shutdown khi nhận `SIGTERM`.
6. Không giới hạn request hoặc chi phí sử dụng agent.
7. State có thể nằm trong memory nên không phù hợp khi scale nhiều instance.

Hardcode secret nguy hiểm vì secret có thể bị đưa lên Git, tồn tại trong lịch
sử commit và bị người khác sử dụng. Secret production phải được truyền qua
environment variables hoặc secret manager.

### Exercise 1.2: Chạy basic version

Phiên bản basic có thể chạy trên localhost, nhưng chưa production-ready vì
thiếu health checks, security, external state, logging và lifecycle management.

### Exercise 1.3: So sánh basic và production

| Feature | Basic | Production | Tại sao quan trọng? |
|---|---|---|---|
| Configuration | Hardcode | Environment variables | Một image dùng được cho local, staging và cloud |
| Secrets | Nằm trong code hoặc file local | Inject từ Render Environment | Tránh lộ credential |
| Health check | Không có | `/health` và `/ready` | Cloud biết khi nào restart hoặc nhận traffic |
| Logging | `print()` | Structured JSON logs | Dễ tìm kiếm và giám sát |
| Shutdown | Dừng đột ngột | FastAPI lifespan + SIGTERM | Đóng Redis và hoàn thành request an toàn |
| State | In-memory | Redis | Nhiều instance dùng chung conversation state |

**Checkpoint 1:** Đã sử dụng environment variables, health/readiness endpoint,
structured logging và graceful shutdown.

---

## Part 2: Docker Containerization

### Exercise 2.1: Dockerfile cơ bản

1. Base image: `python:3.11-slim`.
2. Working directory: `/app`.
3. `requirements.txt` được copy trước source code để Docker cache dependency
   layer. Khi chỉ sửa code, Docker không cần cài lại toàn bộ package.
4. `CMD` cung cấp command mặc định và có thể override khi chạy container.
   `ENTRYPOINT` xác định executable chính và khó thay thế hơn.

### Exercise 2.2: Build và run

Các lệnh sử dụng:

```bash
docker build -t day12-helpdesk-agent .
docker run --rm -p 8000:8000 --env-file .env day12-helpdesk-agent
```

Docker image đã build thành công. Application chạy bằng non-root user
`agent`, expose port `8000` và có Docker `HEALTHCHECK`.

### Exercise 2.3: Multi-stage build

- **Builder stage:** cài compiler và Python dependencies.
- **Runtime stage:** chỉ copy dependencies đã cài và application source.
- Image nhỏ hơn vì compiler, package cache và build tools không xuất hiện
  trong runtime image.
- Image đã kiểm tra có kích thước khoảng `307 MB`, nhỏ hơn yêu cầu `500 MB`.

### Exercise 2.4: Docker Compose stack

```text
Browser / API Client
        |
        v
FastAPI Helpdesk Agent :8000
        |
        v
Redis :6379
  |- Conversation history
  |- Rate-limit windows
  `- Monthly cost usage
```

Service `agent` chỉ khởi động sau khi Redis healthy. Redis sử dụng volume
`redis-data` và AOF để lưu state.

**Checkpoint 2:** Đã hiểu Dockerfile, multi-stage build, Docker Compose,
healthcheck và cách xem logs của container.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway

File `06-lab-complete/railway.toml` khai báo:

- Dockerfile builder.
- Start command sử dụng `$PORT`.
- Health check path `/health`.
- Restart policy khi process lỗi.

Railway phù hợp với deploy nhanh bằng CLI hoặc kết nối GitHub.

### Exercise 3.2: Render

Dự án được deploy thành công bằng Render Blueprint:

- Web service: `day12-helpdesk-agent`.
- Redis/Key Value service: `day12-helpdesk-cache`.
- Region: Singapore.
- Runtime: Docker.
- Branch deploy: `main`.
- Health check: `/health`.

**Public URL:** <https://day12-helpdesk-agent.onrender.com>

Kết quả kiểm tra production:

```json
GET /health
{"status":"ok","version":"2.1.0","agent":"support-supervisor-worker"}
```

```json
GET /ready
{"ready":true,"redis":"connected","llm":"configured"}
```

#### So sánh `render.yaml` và `railway.toml`

| Railway | Render |
|---|---|
| Cấu hình build/deploy cho một service | Blueprint mô tả nhiều resources |
| Có start command và restart policy | Có web service, environment variables và Key Value service |
| Redis thường được thêm trong Railway project | Redis được khai báo trực tiếp bằng `fromService` |
| Deploy qua CLI hoặc GitHub | Blueprint tự đồng bộ từ GitHub |

### Exercise 3.3: Cloud Run CI/CD

`cloudbuild.yaml` mô tả pipeline:

1. Cài dependencies và chạy tests.
2. Build Docker image.
3. Push image lên container registry.
4. Deploy image lên Cloud Run.

`service.yaml` mô tả Cloud Run service, resources, environment variables,
Secret Manager, scaling và health probes. Dự án final chọn Render để deploy
thực tế, nhưng vẫn giữ Cloud Run artifacts để minh họa production CI/CD.

**Checkpoint 3:** Đã deploy thành công, có public URL, environment variables,
Redis service và cloud logs trên Render.

---

## Part 4: API Gateway and Security

Luồng bảo vệ endpoint:

```text
Request
  -> API key authentication
  -> Rate limiting
  -> Input validation
  -> Cost guard
  -> Helpdesk Agent
```

### Exercise 4.1: API Key authentication

- API key được kiểm tra trong `app/auth.py`.
- Header sử dụng: `X-API-Key`.
- Thiếu hoặc sai key trả về HTTP `401`.
- `AGENT_API_KEY` được lấy từ environment variable, không hardcode.
- Rotate key bằng cách tạo key mới trên Render Environment, save/redeploy,
  cập nhật client rồi thu hồi key cũ.

`OPENAI_API_KEY` là server-side secret dùng để gọi OpenAI. Key này không được
nhập vào UI. Người dùng UI chỉ nhập `AGENT_API_KEY`.

### Exercise 4.2: JWT authentication

JWT flow trong ví dụ advanced:

1. Client gửi username/password đến token endpoint.
2. Server xác thực và ký JWT bằng secret.
3. JWT chứa subject, role và thời gian hết hạn.
4. Client gửi `Authorization: Bearer <token>`.
5. Server verify chữ ký và expiry trước khi cho gọi endpoint.

JWT phù hợp khi có nhiều user và role. API key phù hợp cho service-to-service
hoặc một demo agent đơn giản. Dự án final sử dụng API key vì không có hệ thống
tài khoản người dùng; thư viện `PyJWT` vẫn được giữ cho khả năng mở rộng.

### Exercise 4.3: Rate limiting

- Algorithm: Redis sorted-set sliding window.
- Limit mặc định: `10 requests/minute/user_id`.
- Request vượt limit trả về HTTP `429` và header `Retry-After`.
- Redis giúp limit nhất quán khi chạy nhiều API instances.
- Nếu cần bypass cho admin, có thể xác định role sau authentication và áp dụng
  một limit riêng cao hơn. Bản final không cho client tự khai role để tránh
  bypass trái phép.

Kết quả test: các request trong quota trả `200`, request vượt quota trả `429`.

### Exercise 4.4: Cost guard

- Ước lượng chi phí từ input/output tokens.
- Tổng chi phí được lưu trong Redis theo `user_id` và tháng.
- Budget mặc định: `$10/month/user`.
- Khi request làm vượt budget, API trả HTTP `402`.
- Key budget có TTL để tự dọn dữ liệu cũ.

**Checkpoint 4:** Đã implement API key authentication, hiểu JWT flow, dùng
Redis rate limiter và Redis cost guard.

---

## Part 5: Scaling and Reliability

### Exercise 5.1: Health checks

- `/health`: liveness probe, xác nhận process vẫn sống.
- `/ready`: readiness probe, xác nhận application đã startup và báo trạng thái
  Redis cùng LLM configuration.
- Render gọi `/health` để theo dõi service.

### Exercise 5.2: Graceful shutdown

FastAPI lifespan đặt application về trạng thái not-ready, ghi event
`graceful_shutdown` và đóng Redis connection. Uvicorn nhận `SIGTERM` và chạy
lifespan shutdown trước khi process thoát.

Integration test đã gửi shutdown signal và xác nhận log
`graceful_shutdown` xuất hiện.

### Exercise 5.3: Stateless design

Conversation state không nằm trong FastAPI process. Redis lưu:

- Conversation history theo `user_id`.
- Rate-limit sliding window.
- Monthly cost usage.

Vì vậy request tiếp theo có thể được xử lý bởi instance khác mà vẫn đọc được
history trước đó.

### Exercise 5.4: Load balancing

Trong mô hình nhiều replicas, load balancer phân phối request đến các agent
instances. Tất cả instances dùng chung Redis nên không cần sticky session.
Docker Compose và Render thể hiện việc tách application khỏi state service.

### Exercise 5.5: Test stateless

Integration flow đã kiểm tra:

1. Gửi câu hỏi đầu tiên và lưu hai history messages.
2. Gửi follow-up bằng cùng `user_id`.
3. Agent đọc lại history từ Redis.
4. Response chuyển sang route `conversation_context`.
5. `history_count` tăng từ `2` lên `4`.

**Checkpoint 5:** Đã implement liveness/readiness, graceful shutdown,
Redis-backed stateless design và test conversation history.

---

## Part 6: Final Project

Phiên bản mock ban đầu trong `06-lab-complete` đã được thay bằng
**CS + IT Helpdesk Supervisor-Worker Agent** từ VinUni Day 9.

### Agent workflow

1. Supervisor xác định loại yêu cầu.
2. Retrieval worker tìm SLA và knowledge-base evidence.
3. Policy worker kiểm tra refund/access-control policy.
4. Human-review route xử lý yêu cầu rủi ro cao.
5. OpenAI synthesis worker tạo câu trả lời tự nhiên khi LLM được cấu hình.
6. Rule-based synthesis là fallback nếu OpenAI API không khả dụng.

Response bao gồm:

- `answer`
- `route`
- `route_reason`
- `sources`
- `confidence`
- `workers_called`
- `llm_status`
- `trace_id`
- `history_count`

### Production verification

| Kiểm tra | Kết quả |
|---|---|
| Production readiness checker | `20/20` - `100%` |
| Docker multi-stage build | Passed |
| Docker Compose validation | Passed |
| Ruff lint | Passed |
| Unit tests | `7/7` passed |
| Branch coverage | `55%` |
| API không có key | `401` |
| API có key | `200` |
| Rate limit | `429` |
| Cost guard | `402` |
| Redis conversation history | Passed |
| Graceful shutdown | Passed |
| Render `/health` | Passed |
| Render `/ready` | Passed |
| Render HTML UI | Passed |

---

## Bonus Point: GitHub Actions CI/CD

Workflow: `.github/workflows/day12-cicd.yml`

### CI

1. Validate Docker Compose.
2. Build production Docker image.
3. Run Ruff lint.
4. Run `7` unit tests.
5. Enforce branch coverage threshold `55%`.
6. Upload `coverage.xml` artifact.
7. Start Redis and run live integration tests.
8. Run `check_production_ready.py`.

### CD

1. Chỉ chạy sau khi tất cả CI jobs pass.
2. Render tự deploy commit mới từ branch `main`.
3. Workflow hỗ trợ Render Deploy Hook qua secret
   `RENDER_DEPLOY_HOOK_URL`.
4. Sau deploy, workflow kiểm tra public `/health`, `/ready` và HTML UI.

### Demo

- GitHub Actions workflow:
  <https://github.com/letringuyenn/2A202600651_LeTriNguyen_Day12/actions>
- Public application:
  <https://day12-helpdesk-agent.onrender.com>

Kết luận: bản final đáp ứng các yêu cầu productionization, cloud deployment,
security, reliability, stateless scaling và Bonus GitHub Actions CI/CD của
Day 12 lab.
