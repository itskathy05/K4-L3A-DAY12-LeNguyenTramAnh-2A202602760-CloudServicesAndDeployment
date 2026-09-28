from __future__ import annotations

import json
import time
import uuid

import requests
import streamlit as st


DEFAULT_API = "https://day12-agent-production-4b38.up.railway.app"
st.set_page_config(page_title="Cloud Agent Lab · Demo", page_icon="☁️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: radial-gradient(ellipse at 88% 2%, #172c4d 0, transparent 34%), #090e18; color:#e7edf7; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { background:#0d1421; border-right:1px solid #202b3d; }
.hero { padding: 1.5rem 0 1.2rem; border-bottom:1px solid #243047; margin-bottom:1.4rem; }
.eyebrow { color:#70a7ff; font:500 12px 'DM Mono',monospace; letter-spacing:.13em; text-transform:uppercase; }
.hero h1 { font-size:clamp(2.2rem,5vw,3.7rem); letter-spacing:-.055em; line-height:1; margin:.55rem 0; color:#f5f8ff; }
.hero p { color:#98a9c1; font-size:1.02rem; max-width:760px; margin:0; }
.metric { background:linear-gradient(145deg,#121d2e,#0e1725); border:1px solid #26354c; border-radius:14px; padding:16px 18px; min-height:116px; }
.metric-label { color:#8fa2bc; font-size:12px; text-transform:uppercase; letter-spacing:.08em; }
.metric-value { margin-top:10px; color:#eef4ff; font-size:22px; font-weight:700; }
.metric-note { color:#7c8da5; font-size:12px; margin-top:4px; }
.mono { font-family:'DM Mono',monospace; }
div[data-testid="stTabs"] button { color:#9eb0c9; }
div[data-testid="stTabs"] button[aria-selected="true"] { color:#78aaff; }
.small-note { color:#8294ad; font-size:12px; }
</style>
""", unsafe_allow_html=True)

if "events" not in st.session_state:
    st.session_state.events = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None


def base_url() -> str:
    return st.session_state.get("api_base", DEFAULT_API).strip().rstrip("/")


def call_api(method: str, path: str, *, api_key: str = "", user_id: str = "", payload=None):
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    if user_id:
        headers["X-User-Id"] = user_id
    try:
        response = requests.request(method, f"{base_url()}{path}", headers=headers,
                                    json=payload, timeout=20)
        try:
            body = response.json()
        except ValueError:
            body = response.text
        return response.status_code, body
    except requests.RequestException as exc:
        return 0, {"error": str(exc)}


def record(label: str, status: int, body):
    st.session_state.events.insert(0, {
        "time": time.strftime("%H:%M:%S"), "event": label,
        "status": status, "body": body,
    })
    st.session_state.events = st.session_state.events[:12]


def metric(label: str, value: str, note: str):
    st.markdown(f'<div class="metric"><div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
                unsafe_allow_html=True)


with st.sidebar:
    st.markdown("### ☁️ Cloud Agent Lab")
    st.caption("K4 · Level 3A · Day 12")
    st.text_input("API base URL", DEFAULT_API, key="api_base", help="Địa chỉ FastAPI đang deploy.")
    st.markdown("---")
    st.markdown("**Kết nối backend**")
    if st.button("Kiểm tra /health và /ready", use_container_width=True):
        for endpoint in ("/health", "/ready"):
            code, body = call_api("GET", endpoint)
            record(endpoint, code, body)
        st.rerun()
    st.markdown("---")
    st.caption("API key chỉ dùng trong phiên Streamlit hiện tại. Không lưu vào URL hay repository.")

st.markdown("""
<div class="hero"><div class="eyebrow">Production concepts · Live API</div>
<h1>Cloud services<br>in action.</h1>
<p>Demo tương tác cho health/readiness, xác thực API, hội thoại stateless với Redis,
sliding-window rate limit và cost guard.</p></div>
""", unsafe_allow_html=True)

tab_overview, tab_playground, tab_scenarios = st.tabs(["Tổng quan", "API playground", "Tình huống demo"])

with tab_overview:
    c1, c2, c3 = st.columns(3)
    with c1: metric("Liveness · /health", "FastAPI", "Kiểm tra tiến trình còn hoạt động")
    with c2: metric("Readiness · /ready", "Redis", "Kiểm tra service sẵn sàng nhận traffic")
    with c3: metric("Deployment", "Railway · HTTPS", "Mock LLM · shared Redis state")
    st.markdown("#### Request pipeline")
    st.code("POST /ask  →  API key auth  →  sliding-window rate limit  →  monthly cost guard\n"
            "          →  read history  →  mock LLM  →  save conversation + cost  →  JSON log", language="text")
    st.info("/health là liveness probe và không phụ thuộc Redis. /ready kiểm tra Redis; khi dependency lỗi, load balancer nên ngừng gửi traffic tới instance đó.")
    if st.session_state.events:
        st.markdown("#### Hoạt động gần đây")
        for event in st.session_state.events[:5]:
            st.write(f"`{event['time']}` · **{event['event']}** · HTTP {event['status']}")

with tab_playground:
    st.markdown("#### Gửi request tới backend đang deploy")
    st.caption("Để trống API key để xem 401. Key được gửi trong header X-API-Key và không được lưu lại.")
    with st.form("ask_form"):
        key = st.text_input("API key", type="password", autocomplete="new-password")
        col1, col2 = st.columns(2)
        with col1:
            user = st.text_input("User ID", value="sv-demo", max_chars=80,
                                 help="Dùng cùng ID để quan sát history; đây là định danh demo, không phải tài khoản đăng nhập.")
        with col2:
            question = st.text_input("Câu hỏi", value="Xin chào, hãy giải thích readiness check.", max_chars=2000)
        ask_button = st.form_submit_button("Gửi POST /ask", type="primary")
    if ask_button:
        code, body = call_api("POST", "/ask", api_key=key, user_id=user,
                              payload={"question": question})
        record("POST /ask", code, body)
        st.session_state.last_result = (code, body)
    if st.session_state.last_result:
        code, body = st.session_state.last_result
        if code == 200 and isinstance(body, dict):
            st.success(f"HTTP {code} · Request hoàn tất")
            st.markdown(f"**Answer**\n\n{body.get('answer', '')}")
            a, b, c = st.columns(3)
            a.metric("User ID", body.get("user_id", "—"))
            b.metric("History length", body.get("history_length", "—"))
            c.metric("Cost lần này", f"${body.get('cost_usd', 0):.8f}")
            st.json(body.get("tokens", {}))
        else:
            st.error(f"HTTP {code} · {body.get('detail', body) if isinstance(body, dict) else body}")
            with st.expander("Response chi tiết"):
                st.json(body) if isinstance(body, (dict, list)) else st.code(str(body))

with tab_scenarios:
    st.markdown("#### Kịch bản trình bày")
    with st.expander("1 · Liveness và readiness", expanded=True):
        st.write("Gọi hai probe. `/health` trả lời tiến trình còn sống; `/ready` xác nhận Redis có thể phục vụ request.")
        if st.button("Gọi hai health probe"):
            results = []
            for endpoint in ("/health", "/ready"):
                code, body = call_api("GET", endpoint)
                record(endpoint, code, body)
                results.append((endpoint, code, body))
            for endpoint, code, body in results:
                st.write(f"**{endpoint} · HTTP {code}**")
                st.json(body)
    with st.expander("2 · Authentication: thiếu API key → 401"):
        st.write("Gửi request không có X-API-Key để minh họa request bị chặn trước khi xử lý.")
        if st.button("Gửi request không có key", key="unauth"):
            code, body = call_api("POST", "/ask", user_id=f"unauth-{uuid.uuid4().hex[:6]}",
                                  payload={"question": "request không có key"})
            record("POST /ask · no key", code, body)
            st.write(f"HTTP {code}")
            st.json(body)
    with st.expander("3 · Conversation history dùng chung Redis"):
        st.write("Trong API playground, gửi hai câu hỏi liên tiếp với cùng User ID. Lượt sau sẽ báo history_length lớn hơn.")
    with st.expander("4 · Sliding-window rate limit · gọi thật"):
        st.warning("Nút bên dưới gửi tối đa 12 request thật tới production trong vòng một phút. Chúng sẽ tiêu thụ rate limit và ghi history/cost mock cho user riêng.")
        rate_key = st.text_input("API key cho rate limit demo", type="password", key="rate_key")
        if st.button("Tôi hiểu, gửi 12 request thật", type="primary"):
            if not rate_key:
                st.error("Nhập API key trước khi chạy bài thử.")
            else:
                test_user = f"rate-demo-{uuid.uuid4().hex[:8]}"
                results = []
                progress = st.progress(0)
                for i in range(12):
                    code, body = call_api("POST", "/ask", api_key=rate_key,
                                          user_id=test_user,
                                          payload={"question": f"Rate limit demo request {i+1}"})
                    results.append({"request": i + 1, "status": code, "body": body})
                    record(f"rate demo {i+1}/12", code, body)
                    progress.progress((i + 1) / 12)
                    if code == 429:
                        break
                st.write(f"User demo: `{test_user}`")
                st.json(results)
    with st.expander("5 · Cost guard · mô phỏng 402 an toàn"):
        st.write("API hiện không có endpoint để đọc/tăng chi phí tới ngưỡng. Mô phỏng dưới đây chỉ minh họa response 402, không gọi production và không sửa Redis.")
        if st.button("Hiển thị response 402 mô phỏng"):
            st.error("HTTP 402 · monthly budget exceeded")
            st.code(json.dumps({"detail": "monthly budget exceeded"}, indent=2), language="json")

st.markdown("---")
st.markdown('<div class="small-note">Cloud Agent Lab · Streamlit UI · API key không được ghi vào repository.</div>', unsafe_allow_html=True)
