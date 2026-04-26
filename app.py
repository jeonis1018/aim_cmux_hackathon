"""
AI Defense System — Streamlit 웹 인터페이스
터미널(main.py)과 동일한 파이프라인을 웹에서 실행한다.

API 키 로드 우선순위:
  1. Streamlit Cloud secrets  (배포 환경)
  2. 환경변수 ANTHROPIC_API_KEY (일반 서버)
  3. ../api.txt               (로컬 개발)
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import analyze_input
from generator import generate_normal_response
from honey_generator import generate_honey_response
from output_checker import check_output
from attack_logger import log_attack
import config


# ─────────────────────────────────────────────────────────────────────────────
# API 키 로드
# ─────────────────────────────────────────────────────────────────────────────

def get_api_key() -> str | None:
    # 1. Streamlit Cloud secrets
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    # 2. 환경변수
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key
    # 3. 로컬 api.txt
    key_path = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api.txt")
    )
    try:
        with open(key_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 파이프라인 (main.py 와 동일 로직)
# ─────────────────────────────────────────────────────────────────────────────

def handle_safe(user_input: str, api_key: str) -> str | None:
    response = generate_normal_response(user_input, api_key)
    if response is None:
        return None
    return response if check_output(response, api_key) else None


def handle_critical(user_input: str, api_key: str, attempt: int = 1) -> str | None:
    if attempt > config.MAX_HONEYPOT_ATTEMPTS:
        return None
    response = generate_honey_response(user_input, api_key)
    if response is None:
        return handle_critical(user_input, api_key, attempt + 1)
    return response if check_output(response, api_key) else handle_critical(user_input, api_key, attempt + 1)


# ─────────────────────────────────────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Defense System",
    page_icon="🛡️",
    layout="centered",
)

# ─────────────────────────────────────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🛡️ AI Defense System")
    st.caption("AI Safety Hackathon")
    st.divider()

    st.markdown("**파이프라인**")
    st.markdown(
        "1. 입력 분석기 → SAFE / CRITICAL 분류  \n"
        "2. 정상 생성기 *or* 허니팟 생성기  \n"
        "3. 출력 검사기 → 정답 누출 탐지"
    )
    st.divider()

    if config.INPUT_CHECKER_ENABLED:
        st.success("입력 검사기: ON")
    else:
        st.warning("입력 검사기: OFF (모든 입력 → 정상 경로)")

    st.divider()
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# API 키 확인
# ─────────────────────────────────────────────────────────────────────────────

api_key = get_api_key()
if not api_key:
    st.error(
        "API 키를 찾을 수 없습니다.  \n"
        "Streamlit Cloud → App settings → Secrets 에서 `ANTHROPIC_API_KEY`를 설정해주세요."
    )
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 채팅 UI
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("## 🛡️ AI Defense System")
st.caption("입력 검사 · 출력 검사 · 허니팟 기반 AI 방어 데모")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 렌더링
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("classification"):
            if msg["classification"] == "CRITICAL":
                st.error(f"분류: {msg['classification']} — 허니팟 응답 제공됨", icon="🍯")
            else:
                st.success(f"분류: {msg['classification']}", icon="✅")
        st.markdown(msg["content"])

# 입력창
if user_input := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 어시스턴트 응답 처리
    with st.chat_message("assistant"):
        with st.spinner("분석 중..."):

            # Step 1: 입력 분류
            if config.INPUT_CHECKER_ENABLED:
                classification = analyze_input(user_input, api_key)
            else:
                classification = "SAFE"

            # Step 2: 경로 분기
            if classification == "SAFE":
                response = handle_safe(user_input, api_key)
            else:
                response = handle_critical(user_input, api_key)
                log_attack(user_input, response)

            # Step 3: 출력
            if classification == "CRITICAL":
                st.error(f"분류: {classification} — 허니팟 응답 제공됨", icon="🍯")
            else:
                st.success(f"분류: {classification}", icon="✅")

            if response:
                content = response
            else:
                content = "죄송합니다, 해당 정보는 제공할 수 없습니다."

            st.markdown(content)

    st.session_state.messages.append({
        "role": "assistant",
        "content": content,
        "classification": classification,
    })
