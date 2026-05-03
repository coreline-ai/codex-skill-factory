#!/usr/bin/env python3
from __future__ import annotations

import datetime
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

TEST_RE = re.compile(r"\b(pytest|npm test|pnpm test|yarn test|jest|vitest)\b", re.IGNORECASE)
LINT_RE = re.compile(r"\b(ruff check|eslint|mypy|tsc|typecheck|lint|prettier)\b", re.IGNORECASE)


def read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except Exception:
        return {"raw": raw}
    return value if isinstance(value, dict) else {"raw": value}


def redact_secrets(text: str) -> str:
    redacted = text or ""
    for pattern in SECRET_PATTERNS:
        redacted = re.sub(pattern, "[REDACTED_SECRET]", redacted)
    return redacted


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


def get_nested(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_value(payload: dict[str, Any], paths: list[tuple[str, ...]]) -> Any:
    for path in paths:
        value = get_nested(payload, *path)
        if value not in (None, ""):
            return value
    return None


def extract_command(payload: dict[str, Any]) -> str:
    value = first_value(
        payload,
        [
            ("command",),
            ("cmd",),
            ("tool_input", "command"),
            ("tool_input", "cmd"),
            ("input", "command"),
            ("arguments", "command"),
            ("params", "command"),
        ],
    )
    if value is None:
        return ""
    if isinstance(value, list):
        return redact_secrets(" ".join(str(item) for item in value))
    return redact_secrets(str(value))


def extract_exit_code(payload: dict[str, Any]) -> int | None:
    value = first_value(
        payload,
        [
            ("exit_code",),
            ("return_code",),
            ("returncode",),
            ("result", "exit_code"),
            ("tool_result", "exit_code"),
            ("output", "exit_code"),
        ],
    )
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    return None


def infer_success(payload: dict[str, Any], exit_code: int | None) -> bool | None:
    if exit_code is not None:
        return exit_code == 0
    value = first_value(payload, [("success",), ("ok",), ("result", "success"), ("tool_result", "success")])
    if isinstance(value, bool):
        return value
    status = str(first_value(payload, [("status",), ("result", "status"), ("tool_result", "status")]) or "").lower()
    if status in {"success", "succeeded", "ok", "passed", "pass"}:
        return True
    if status in {"failure", "failed", "error", "errored", "timeout"}:
        return False
    return None


def output_tail(payload: dict[str, Any], limit: int = 4000) -> str:
    value = first_value(
        payload,
        [
            ("output",),
            ("stdout",),
            ("stderr",),
            ("result", "output"),
            ("tool_result", "output"),
            ("result", "stdout"),
            ("tool_result", "stdout"),
        ],
    )
    if value is None:
        return ""
    text = redact_secrets(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False))
    return text[-limit:]


def get_changed_files(repo_root: str) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo_root, stderr=subprocess.DEVNULL, text=True
        )
    except Exception:
        return []
    files: list[str] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path and path not in files:
            files.append(path)
    return files


def main() -> int:
    payload = read_stdin_json()
    cwd = str(payload.get("cwd") or os.getcwd())
    repo_root = get_repo_root(cwd)
    command = extract_command(payload)
    exit_code = extract_exit_code(payload)
    success = infer_success(payload, exit_code)
    tool_name = str(
        first_value(payload, [("tool_name",), ("tool",), ("name",), ("tool_call", "name")]) or "unknown"
    )
    changed_files = get_changed_files(repo_root)
    log_dir = pathlib.Path(repo_root) / ".codex-prompt-history"
    log_dir.mkdir(parents=True, exist_ok=True)

    entry = {
        "id": f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-tool",
        "timestamp": utc_now(),
        "event": "PostToolUse",
        "hook_event_name": payload.get("hook_event_name"),
        "session_id": payload.get("session_id"),
        "turn_id": payload.get("turn_id"),
        "cwd": cwd,
        "repo_root": repo_root,
        "git_branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root),
        "git_commit": git_value(["rev-parse", "--short", "HEAD"], cwd=repo_root),
        "model": payload.get("model"),
        "tool_name": tool_name,
        "command": command,
        "exit_code": exit_code,
        "success": success,
        "is_test_command": bool(TEST_RE.search(command)),
        "is_lint_command": bool(LINT_RE.search(command)),
        "changed_files": changed_files,
        "changed_file_count": len(changed_files),
        "output_tail": output_tail(payload),
        "raw_payload_keys": sorted(list(payload.keys())),
    }
    with (log_dir / "tool_uses.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
