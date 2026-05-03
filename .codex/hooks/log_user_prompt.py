#!/usr/bin/env python3
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{20,}",
    r"ghp_[A-Za-z0-9_]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"xox[baprs]-[A-Za-z0-9\-]+",
    r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s]+",
    r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._\-]+",
]

FILE_PATTERN = re.compile(
    r"(?P<path>(?:[\w.\-]+/)*[\w.\-]+\.(?:py|ts|tsx|js|jsx|md|json|yaml|yml|toml|sql|html|css|go|rs|java|kt|swift|php|rb|c|cpp|h))"
)


def read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except Exception:
        return {"raw": raw}
    return value if isinstance(value, dict) else {"raw": value}


def git_value(args: list[str], cwd: str | None = None) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=cwd, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return None


def get_repo_root(cwd: str) -> str:
    return git_value(["rev-parse", "--show-toplevel"], cwd=cwd) or cwd


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def stringify_prompt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def redact_secrets(text: str) -> str:
    redacted = text or ""
    for pattern in SECRET_PATTERNS:
        redacted = re.sub(pattern, "[REDACTED_SECRET]", redacted)
    return redacted


def extract_files(text: str) -> list[str]:
    found: list[str] = []
    for match in FILE_PATTERN.finditer(text or ""):
        value = match.group("path")
        if value not in found:
            found.append(value)
    return found


def normalize_prompt(text: str) -> str:
    normalized = (text or "").lower().strip()
    normalized = re.sub(r"`[^`]+`", "<code>", normalized)
    normalized = FILE_PATTERN.sub("<file>", normalized)
    normalized = re.sub(r"https?://\S+", "<url>", normalized)
    normalized = re.sub(r"\b[0-9a-f]{7,40}\b", "<hash>", normalized)
    normalized = re.sub(r"\b\d+\b", "<num>", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    replacements = {
        "고쳐줘": "수정",
        "고쳐": "수정",
        "수정해줘": "수정",
        "해결해줘": "해결",
        "만들어줘": "생성",
        "작성해줘": "작성",
        "분석해줘": "분석",
        "검토해줘": "검토",
        "알려줘": "설명",
        "해줘": "",
    }
    for src, dst in replacements.items():
        normalized = normalized.replace(src, dst)
    return normalized.strip()


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def detect_language(text: str) -> str:
    return "ko" if re.search(r"[가-힣]", text or "") else "en"


def main() -> int:
    payload = read_stdin_json()
    cwd = stringify_prompt(payload.get("cwd")) or os.getcwd()
    repo_root = get_repo_root(cwd)
    prompt_raw = stringify_prompt(payload.get("prompt") or payload.get("user_prompt") or "")
    prompt_redacted = redact_secrets(prompt_raw)
    normalized = normalize_prompt(prompt_redacted)

    log_dir = pathlib.Path(repo_root) / ".codex-prompt-history"
    log_dir.mkdir(parents=True, exist_ok=True)

    entry = {
        "id": f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{short_hash(prompt_redacted)}",
        "timestamp": utc_now(),
        "event": "UserPromptSubmit",
        "hook_event_name": payload.get("hook_event_name"),
        "session_id": payload.get("session_id"),
        "turn_id": payload.get("turn_id"),
        "cwd": cwd,
        "repo_root": repo_root,
        "git_branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root),
        "git_commit": git_value(["rev-parse", "--short", "HEAD"], cwd=repo_root),
        "model": payload.get("model"),
        "prompt_redacted": prompt_redacted,
        "normalized_prompt": normalized,
        "prompt_hash": short_hash(normalized),
        "files_mentioned": extract_files(prompt_redacted),
        "language": detect_language(prompt_redacted),
        "raw_payload_keys": sorted(list(payload.keys())),
    }
    with (log_dir / "prompts.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
