"""
공격 로거 (Attack Logger)
CRITICAL 로 분류된 입력(허니팟 경로)을 attack_log.json 에 기록한다.

JSON 구조:
{
  "attacks": [
    {
      "id": 1,
      "timestamp": "2026-04-26T15:30:00.123456",
      "input": "공격자 입력",
      "honey_response": "허니팟 응답 (거부 시 null)"
    },
    ...
  ]
}

파일이 없으면 새로 생성, 있으면 마지막 id + 1 로 추가.
"""

import json
import os
from datetime import datetime

from config import debug

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attack_log.json")


def log_attack(user_input: str, honey_response: str | None) -> int:
    """
    공격 기록을 JSON 파일에 저장하고 부여된 id를 반환한다.
    """
    # ── 기존 데이터 로드 ─────────────────────────────────────────────────────
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "attacks" not in data or not isinstance(data["attacks"], list):
                data = {"attacks": []}
        except (json.JSONDecodeError, OSError) as e:
            debug(f"attack_log.json read error ({e}) — starting fresh")
            data = {"attacks": []}
    else:
        data = {"attacks": []}

    # ── 다음 id 계산 ─────────────────────────────────────────────────────────
    if data["attacks"]:
        next_id = max(entry.get("id", 0) for entry in data["attacks"]) + 1
    else:
        next_id = 1

    # ── 새 항목 추가 ─────────────────────────────────────────────────────────
    entry = {
        "id": next_id,
        "timestamp": datetime.now().isoformat(),
        "input": user_input,
        "honey_response": honey_response,
    }
    data["attacks"].append(entry)

    # ── 저장 ─────────────────────────────────────────────────────────────────
    try:
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        debug(f"Attack logged → id={next_id}  path={LOG_PATH}")
    except OSError as e:
        debug(f"attack_log.json write error: {e}")

    return next_id
