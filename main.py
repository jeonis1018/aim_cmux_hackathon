"""
AI Defense System — 메인 진입점

파이프라인:
  입력 → [입력 분석기] → SAFE  → [정상 생성기] → [출력 검사기] → 출력 or 거부
                       → CRITICAL → [허니팟 생성기] → [출력 검사기] → 출력 or 재시도(max 3) or 거부

api.txt 위치: 이 파일 기준 ../api.txt  (aim_cmux/api.txt)
"""

import os
import sys

# Windows 터미널 UTF-8 출력 보장
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from analyzer import analyze_input
from generator import generate_normal_response
from honey_generator import generate_honey_response
from output_checker import check_output
from attack_logger import log_attack
from config import MAX_HONEYPOT_ATTEMPTS, DEBUG, INPUT_CHECKER_ENABLED, debug


# ─────────────────────────────────────────────────────────────────────────────
# API 키 로드
# ─────────────────────────────────────────────────────────────────────────────

def load_api_key() -> str:
    key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api.txt")
    key_path = os.path.normpath(key_path)
    try:
        with open(key_path, "r", encoding="utf-8") as f:
            key = f.read().strip()
        debug(f"API key loaded from: {key_path}  (length: {len(key)})")
        return key
    except FileNotFoundError:
        print(f"[ERROR] api.txt not found at: {key_path}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# SAFE 경로 처리
# ─────────────────────────────────────────────────────────────────────────────

def handle_safe(user_input: str, api_key: str) -> str | None:
    debug("--- SAFE Path ---")

    # 1. 정상 응답 생성
    response = generate_normal_response(user_input, api_key)
    if response is None:
        debug("Normal generator returned None")
        return None

    # 2. 출력 검사
    safe = check_output(response, api_key)
    if safe:
        debug("Output check: PASSED ✓")
        return response
    else:
        debug("Output check: FAILED ✗ — refusing")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL 경로 처리 (허니팟 + 재귀)
# ─────────────────────────────────────────────────────────────────────────────

def handle_critical(user_input: str, api_key: str, attempt: int = 1) -> str | None:
    if attempt > MAX_HONEYPOT_ATTEMPTS:
        debug(f"Max honeypot attempts ({MAX_HONEYPOT_ATTEMPTS}) exceeded — refusing")
        return None

    debug(f"--- CRITICAL / Honeypot Path  [attempt {attempt}/{MAX_HONEYPOT_ATTEMPTS}] ---")

    # 1. 허니팟 응답 생성
    response = generate_honey_response(user_input, api_key)
    if response is None:
        debug("Honey generator returned None — retrying")
        return handle_critical(user_input, api_key, attempt + 1)

    # 2. 출력 검사 (실제 flag 가 실수로 포함됐는지 확인)
    safe = check_output(response, api_key)
    if safe:
        debug("Output check: PASSED ✓ (fake flag, no real info leaked)")
        return response
    else:
        debug("Output check: FAILED ✗ (real flag leaked in honey response) — retrying")
        return handle_critical(user_input, api_key, attempt + 1)


# ─────────────────────────────────────────────────────────────────────────────
# 메인 루프
# ─────────────────────────────────────────────────────────────────────────────

def main():
    api_key = load_api_key()

    print("=" * 62)
    print("   AI Defense System  |  AI Safety Hackathon")
    print("=" * 62)
    if DEBUG:  # 제출 전 이 if 블록 주석처리
        print("[DEBUG MODE — set DEBUG=False in config.py before submission]\n")
    print("메시지를 입력하세요. 종료: quit\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        print()

        # ── Step 1: 입력 분류 ────────────────────────────────────────────────
        if INPUT_CHECKER_ENABLED:
            debug("Step 1 — Input classification (checker ON)")
            classification = analyze_input(user_input, api_key)
        else:
            debug("Step 1 — Input checker DISABLED: routing to SAFE")
            classification = "SAFE"

        checker_status = "ON" if INPUT_CHECKER_ENABLED else "OFF"
        if DEBUG == True:
            print(f"[ANALYSIS] Classification: {classification}  (input checker: {checker_status})")
            print()

        # ── Step 2 / 3: 경로 분기 ────────────────────────────────────────────
        if classification == "SAFE":
            response = handle_safe(user_input, api_key)
        else:
            response = handle_critical(user_input, api_key)
            attack_id = log_attack(user_input, response)
            debug(f"Attack saved to attack_log.json  (id={attack_id})")

        # ── 최종 출력 ────────────────────────────────────────────────────────
        print()
        if response:
            print(f"Assistant: {response}")
        else:
            print("Assistant: 죄송합니다, 해당 정보는 제공할 수 없습니다.")

        print("\n" + "─" * 62 + "\n")


if __name__ == "__main__":
    main()
