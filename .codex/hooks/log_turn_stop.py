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

TEST_RE = re.compile(r"\b(pytest|npm test|pnpm test|yarn test|jest|vitest)\b", re.IGNORECASE)
LINT_RE = re.compile(r"\b(ruff check|eslint|mypy|tsc|typecheck|lint|prettier)\b", re.IGNORECASE)
REPEAT_FIX_RE = re.compile(
    r"(재수정|다시\s*고쳐|또\s*실패|여전히|아직|same issue|still failing|fix again|regression)",
    re.IGNORECASE,
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


def payload_text(payload: dict[str, Any]) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False)
    except Exception:
        return str(payload)


def extract_commands_from_payload(payload: dict[str, Any]) -> list[str]:
    text = payload_text(payload)
    commands: list[str] = []
    patterns = [
        r"pytest[^\n\"']*",
        r"npm test[^\n\"']*",
        r"pnpm test[^\n\"']*",
        r"yarn test[^\n\"']*",
        r"ruff check[^\n\"']*",
        r"eslint[^\n\"']*",
        r"tsc[^\n\"']*",
        r"mypy[^\n\"']*",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = match.group(0).strip()
            if value not in commands:
                commands.append(value)
    return commands[:20]


def extract_exit_codes(payload: dict[str, Any]) -> list[int]:
    text = payload_text(payload)
    values: list[int] = []
    for pattern in (r'"exit_code"\s*:\s*(-?\d+)', r'"return_code"\s*:\s*(-?\d+)', r'"returncode"\s*:\s*(-?\d+)'):
        for match in re.finditer(pattern, text):
            value = int(match.group(1))
            if value not in values:
                values.append(value)
    for key in ("exit_code", "return_code", "returncode"):
        value = payload.get(key)
        if isinstance(value, int) and value not in values:
            values.append(value)
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            parsed = int(value)
            if parsed not in values:
                values.append(parsed)
    return values[:20]


def infer_success(payload: dict[str, Any], exit_codes: list[int]) -> bool | None:
    if exit_codes:
        return all(code == 0 for code in exit_codes)
    for key in ("success", "ok"):
        if isinstance(payload.get(key), bool):
            return payload[key]
    status = str(payload.get("status") or payload.get("result") or "").lower()
    if status in {"success", "succeeded", "ok", "passed", "pass"}:
        return True
    if status in {"failure", "failed", "error", "errored", "timeout"}:
        return False
    return None


def main() -> int:
    payload = read_stdin_json()
    cwd = str(payload.get("cwd") or os.getcwd())
    repo_root = get_repo_root(cwd)
    log_dir = pathlib.Path(repo_root) / ".codex-prompt-history"
    log_dir.mkdir(parents=True, exist_ok=True)

    changed_files = get_changed_files(repo_root)
    commands_seen = extract_commands_from_payload(payload)
    exit_codes = extract_exit_codes(payload)
    success = infer_success(payload, exit_codes)
    text = payload_text(payload)
    has_test_signal = bool(TEST_RE.search(" ".join(commands_seen) or text))
    has_lint_signal = bool(LINT_RE.search(" ".join(commands_seen) or text))

    entry = {
        "id": f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-stop",
        "timestamp": utc_now(),
        "event": "Stop",
        "hook_event_name": payload.get("hook_event_name"),
        "session_id": payload.get("session_id"),
        "turn_id": payload.get("turn_id"),
        "cwd": cwd,
        "repo_root": repo_root,
        "git_branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root),
        "git_commit": git_value(["rev-parse", "--short", "HEAD"], cwd=repo_root),
        "model": payload.get("model"),
        "changed_files": changed_files,
        "changed_file_count": len(changed_files),
        "commands_seen": commands_seen,
        "exit_codes_seen": exit_codes,
        "success": success,
        "has_test_signal": has_test_signal,
        "test_passed": success if has_test_signal else None,
        "has_lint_signal": has_lint_signal,
        "lint_passed": success if has_lint_signal else None,
        "repeat_fix_signal": bool(REPEAT_FIX_RE.search(text)),
        "summary": "Codex turn stopped",
        "raw_payload_keys": sorted(list(payload.keys())),
    }
    with (log_dir / "turns.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
