# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng `> *Câu trả lời của bạn*` bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Lê Nguyễn Trâm Anh  
> Mã học viên: 2A202602760

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Khi deploy, nếu tôi quên set `AGENT_API_KEY`, service dừng ngay trong giai đoạn
> khởi động và log chỉ rõ biến bị thiếu. Nhờ vậy bản deploy lỗi không được
> nhận traffic. Nếu có mặc định `"changeme"`, service vẫn chạy và endpoint `/ask`
> sẽ được bảo vệ bằng một khóa ai cũng có thể đoán, dẫn đến lộ dịch vụ và
> phát sinh chi phí.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Log tôi thu được khi gọi thử `/ask`:
> `{"event":"ask_completed","level":"info","timestamp":"2026-09-28T07:41:50.190585+00:00","user_id":"manual-check","tokens_in":4,"tokens_out":43,"cost_usd":2.64e-05}`.
> Với JSON này, hệ thống log có thể lọc theo `event`/`user_id` và tổng hợp
> `cost_usd` để cảnh báo chi phí. Chuỗi `print("\u0111ã trả lời xong")` không có
> các trường máy đọc để thực hiện hai việc đó.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 1.73 GB (khoảng 1730 MB) |
| Multi-stage | 271 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Tôi đo bằng `docker images`: `day12-agent:single` là 1.73 GB, còn
> `day12-agent:prod` là 271 MB. Bản single-stage dùng image Python đầy đủ và giữ
> toàn bộ môi trường cài đặt. Bản multi-stage dùng image slim và chỉ copy dependency
> đã cài sang runtime, nên không mang các thành phần build không cần thiết.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Sau khi tôi thêm một dòng comment tạm vào `app/main.py`, Docker báo các
> layer base image, `COPY requirements.txt` và `pip install` đều `CACHED`. Chỉ layer
> copy `app`, copy `utils` phía sau nó và export image chạy lại. Nếu `COPY . .`
> nằm trước `RUN pip install`, mọi thay đổi source sẽ làm mất cache của layer copy,
> kéo theo `pip install` phải chạy lại dù `requirements.txt` không thay đổi.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Kẻ tấn công có thể khai thác lỗ hổng trong API Python để thực thi lệnh
> trong container. Nếu process chạy root, lệnh đó có quyền root trong container;
> khi kết hợp thêm lỗ hổng container runtime hoặc mount nhạy cảm, kẻ tấn công có
> thể tác động tới host với quyền cao. `USER app` cắt chuỗi này tại bước
> thực thi trong container: process bị giới hạn bởi quyền của user `app`.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> Người dùng có thể gửi 20 request trong 2 giây: 10 request vào giây 59
> của phút trước, sau đó bộ đếm reset và gửi thêm 10 request vào giây 00
> của phút sau. Sliding window nhìn lại 60 giây từng thời điểm nên không tạo
> ra khe hở ở ranh giới hai phút như vậy.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> Rate limit giới hạn tần suất trong cửa sổ 60 giây, còn cost guard giới hạn
> tổng tiền theo user trong tháng. Một user gửi chỉ 1 request/phút nhưng request rất
> tốn token thì rate limit cho qua trong khi cost guard có thể chặn. Ngược lại, user
> còn nhiều ngân sách nhưng gửi 11 request nhỏ trong cùng một phút thì cost guard
> vẫn cho phép về mặt chi phí, còn rate limit 10/phút chặn request thứ 11.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Nếu gộp probe và cho nó ping Redis, khi Redis mất kết nối thì cả ba container
> cùng báo unhealthy. Orchestrator coi cả ba process bị hỏng và restart chúng, dù
> code API vẫn sống. Các container mới lại ping Redis đang lỗi và tiếp tục bị restart,
> tạo vòng lặp và làm toàn bộ service gián đoạn. Khi tách probe, `/health` vẫn
> 200 nên container không bị restart; `/ready` trả 503 để load balancer tạm ngừng
> gửi traffic cho đến khi Redis phục hồi.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Tôi chạy ba container trên các cổng 8011, 8012 và 8013, cùng trỏ tới một
> Redis và gửi cùng `X-User-Id`. Ba response lần lượt có `history_length` là
> 0, 2 và 4, chứng tỏ instance sau đọc được dữ liệu instance trước đã ghi.
> Nếu dùng dict Python, mỗi container có dict riêng; request rơi vào instance khác
> sẽ thấy history bị quay về 0 hoặc tăng không liên tục.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> *Câu trả lời của bạn*
