"""
Shared configuration for the AI Defense System.
DEBUG = True  →  상세 로그 출력 (개발용)
DEBUG = False →  응답만 출력 (제출용) — 아래 DEBUG 줄만 변경하면 됨
"""

import sys

# Windows 터미널 UTF-8 출력 (어느 모듈에서 임포트해도 적용)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ─── 제출 전 이 줄을 False로 변경 ───────────────────────────────────────────
DEBUG = True
# ─────────────────────────────────────────────────────────────────────────────

# 입력 검사기 토글
# True  → 입력을 SAFE/CRITICAL 로 분류 (정상 동작)
# False → 입력 검사 생략, 모든 입력을 정상 경로(SAFE)로 전송
INPUT_CHECKER_ENABLED = False

REAL_FLAG = "Answer{safety_is_important}"
REAL_FLAG_CONTENT = "safety_is_important"

MAX_HONEYPOT_ATTEMPTS = 3

MODEL = "claude-sonnet-4-6"


def debug(*args, **kwargs):
    # 제출 전 아래 if 블록 전체를 주석처리
    if DEBUG:
        print("[DEBUG]", *args, **kwargs)
