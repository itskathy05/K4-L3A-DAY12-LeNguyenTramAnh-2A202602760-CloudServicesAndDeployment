# Báo cáo Lab: Cloud Services and Deployment

## 1. Thông tin bài làm

| Mục | Nội dung |
|---|---|
| Học viên | Lê Nguyễn Trâm Anh |
| Mã học viên | 2A202602760 |
| Repository | [K4-L3A-DAY12-LeNguyenTramAnh-2A202602760-CloudServicesAndDeployment](https://github.com/itskathy05/K4-L3A-DAY12-LeNguyenTramAnh-2A202602760-CloudServicesAndDeployment) |
| Nền tảng cloud | Railway |
| Public API | [https://day12-agent-production-4b38.up.railway.app](https://day12-agent-production-4b38.up.railway.app) |
| Ngày xác minh | 2026-09-28 |

## 2. Mục tiêu và kiến trúc

Lab đưa một AI agent dạng HTTP API từ môi trường local lên cloud. Hệ thống áp dụng cấu hình qua biến môi trường, đóng gói Docker, xác thực API, giới hạn tốc độ và ngân sách, lưu state dùng chung trong Redis, health/readiness probe và xử lý graceful shutdown. Agent dùng mock LLM do lab cung cấp nên không cần API key của nhà cung cấp mô hình.

Trên Railway, FastAPI chạy trong service `day12-agent` và Redis chạy thành service riêng. Agent nhận request HTTPS; Redis lưu hội thoại, cửa sổ rate limit và chi phí theo tháng. Giao diện demo web được phục vụ tại [`/demo`](https://day12-agent-production-4b38.up.railway.app/demo). Mã nguồn có thêm Streamlit demo tại [`streamlit_app/app.py`](https://github.com/itskathy05/K4-L3A-DAY12-LeNguyenTramAnh-2A202602760-CloudServicesAndDeployment/blob/main/streamlit_app/app.py), dùng cùng API production.

Luồng `POST /ask` gồm: xác thực `X-API-Key` → rate limit theo user → cost guard theo tháng UTC → đọc history Redis → gọi mock LLM → lưu hai lượt hội thoại và chi phí → ghi log JSON → trả response có answer, user ID, độ dài history, cost và token.

## 3. Kết quả theo checkpoint

### CP1 — Cấu hình, health check và logging

`Settings` đọc cấu hình từ environment; `AGENT_API_KEY` là biến bắt buộc và không có giá trị mặc định. `/health` là liveness probe độc lập với Redis. Log sự kiện xuất ra stdout dưới dạng JSON một dòng, gồm event, log level thường, timestamp UTC và dữ liệu theo request.

### CP2 — Docker và Compose

Dockerfile multi-stage dùng Python 3.11 slim. Builder cài dependency trước khi copy mã nguồn; runtime chỉ nhận phần cần thiết, chạy bằng user không phải root và có HTTP healthcheck không cần `curl`. Compose ghép agent với Redis; `.dockerignore` loại secret, Git metadata, virtualenv và cache khỏi build context.

Docker build và toàn bộ 16 test CP2 đều thành công. Kích thước đo bằng Docker:

| Image | Kích thước |
|---|---:|
| Single-stage `day12-agent:single` | 1.73 GB |
| Multi-stage `day12-agent:prod` | 271 MB |

### CP3 — API security

`POST /ask` yêu cầu API key và so sánh an toàn; request thiếu hoặc sai key bị từ chối. Sliding window dùng Redis sorted set, tách theo user và giới hạn mặc định 10 request trong 60 giây. Cost guard theo dõi ngân sách mặc định 10 USD/user/tháng UTC, kiểm tra trước khi gọi LLM và ghi nhận chi phí sau đó.

### CP4 — Stateless và reliability

Conversation store lưu JSON trong Redis List, tối đa 20 message/user, TTL 7 ngày. `/ready` xác nhận Redis có thể phục vụ request; `/health` chỉ theo dõi tiến trình. Khi nhận SIGTERM/SIGINT, service chuyển sang trạng thái draining để hai probe trả trạng thái không sẵn sàng trong lúc hoàn tất request đang chạy.

Trong thử nghiệm ba instance dùng chung Redis, `history_length` lần lượt là 0, 2 và 4. Kết quả cho thấy history được chia sẻ qua Redis thay vì phụ thuộc bộ nhớ của từng process.

### CP5 — Deploy Railway

Railway cấp `PORT`; `REDIS_URL` tham chiếu tới service Redis. Các cấu hình deploy dùng `AGENT_API_KEY`, `RATE_LIMIT_PER_MINUTE`, `MONTHLY_BUDGET_USD`, `LOG_LEVEL` và `RAILWAY_DEPLOYMENT_DRAINING_SECONDS`. Giá trị secret được giữ trong cấu hình Railway/GitHub Secrets, không ghi trong tài liệu.

Kiểm tra live ngày 2026-09-28:

| Request | Kết quả |
|---|---|
| `GET /health` | HTTP 200, `status: ok` |
| `GET /ready` | HTTP 200, `status: ready`, `redis: true` |
| `POST /ask` không có key | HTTP 401 |
| `POST /ask` với key hợp lệ | HTTP 200 và có câu trả lời |

Test CP5 chạy trên deployment thật: **9 passed**. Bốn test local fallback được skip vì đang xác minh cấu hình cloud.

## 4. Bài phản ánh

`exercises.md` có đủ 10 câu trả lời, đi từ fail-fast config và log JSON đến Docker, rate limit, cost guard, probes, Redis history và lần triển khai Railway. Ví dụ log và kết quả đo image/history trong câu trả lời dựa trên các lần chạy ghi nhận trong quá trình làm lab.

## 5. Bonus CI/CD

GitHub Actions chạy test khi push hoặc pull request vào `main`, build Docker image sau khi test đạt, rồi deploy Railway khi push lên `main` và các job trước đó thành công. Railway token được đọc từ repository secret `RAILWAY_TOKEN`; README có badge workflow.

Workflow badge hiện báo passing. Bộ kiểm tra bonus đạt **13/13**, gồm trigger, test/build/deploy dependency, giới hạn deploy vào `main`, secret handling, action version pinning và badge.

## 6. Kiểm thử và điểm

Đã chạy `python grade.py` ngày 2026-09-28 với Docker Desktop và kết nối internet:

| Phần | Kết quả | Điểm |
|---|---:|---:|
| CP1 | 13/13 | 15/15 |
| CP2 | 16/16 | 15/15 |
| CP3 | 22/22 | 20/20 |
| CP4 | 19/19 | 20/20 |
| CP5 | 9/9 (4 bài fallback được skip) | 15/15 |
| Exercises | 10/10 câu | 15/15 |
| Bonus CI/CD | 13/13 | +10/10 |
| **Tổng bắt buộc** | | **100/100** |
| **Tổng cuối theo trần của lab** | | **100/100** |

## 7. Bằng chứng

- [Railway dashboard](screenshots/dashboard.png)
- [Health endpoint](screenshots/health.png)
- [GitHub Actions workflow](https://github.com/itskathy05/K4-L3A-DAY12-LeNguyenTramAnh-2A202602760-CloudServicesAndDeployment/actions)
- [Streamlit UI source](streamlit_app/app.py)

## 8. Kết luận

Các checkpoint CP1–CP5 và bonus CI/CD đạt kết quả đầy đủ theo grader: phần bắt buộc **100/100**, bonus **10/10** trước khi áp dụng trần điểm tổng. API production chạy trên Railway qua HTTPS, kết nối Redis, yêu cầu API key cho endpoint nghiệp vụ và có health/readiness probe. Image multi-stage nhỏ hơn 500 MB; workflow tự động kiểm tra, build và deploy sau khi các bước trước đạt.
