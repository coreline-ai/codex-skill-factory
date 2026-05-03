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

from .storage import get_paths

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{20,}",
    r"ghp_[A-Za-z0-9_]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"xox[baprs]-[A-Za-z0-9\-]+",
    r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s]+",
    r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._\-]+",
]

FILE_RE = re.compile(
    r"(?P<path>(?:[\w.\-]+/)*[\w.\-]+\.(?:py|ts|tsx|js|jsx|md|json|yaml|yml|toml|sql|html|css|go|rs|java|kt|swift|php|rb|c|cpp|h))"
)
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


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def git_value(args: list[str], cwd: str | None = None) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=cwd, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return None


def repo_root_from_cwd(cwd: str) -> pathlib.Path:
    return pathlib.Path(git_value(["rev-parse", "--show-toplevel"], cwd=cwd) or cwd).resolve()


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def redact_secrets(text: str) -> str:
    redacted = text or ""
    for pattern in SECRET_PATTERNS:
        redacted = re.sub(pattern, "[REDACTED_SECRET]", redacted)
    return redacted


def normalize_prompt(text: str) -> str:
    normalized = (text or "").lower().strip()
    normalized = re.sub(r"`[^`]+`", "<code>", normalized)
    normalized = FILE_RE.sub("<file>", normalized)
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


def extract_files(text: str) -> list[str]:
    found: list[str] = []
    for match in FILE_RE.finditer(text or ""):
        value = match.group("path")
        if value not in found:
            found.append(value)
    return found


def get_changed_files(repo_root: pathlib.Path) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
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


def infer_success(payload: dict[str, Any], exit_code: int | None = None) -> bool | None:
    if exit_code is not None:
        return exit_code == 0
    value = first_value(payload, [("success",), ("ok",), ("result", "success"), ("tool_result", "success")])
    if isinstance(value, bool):
        return value
    status = str(
        first_value(payload, [("status",), ("result", "status"), ("tool_result", "status")]) or ""
    ).lower()
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


def hook_paths(payload: dict[str, Any], project: bool) -> tuple[pathlib.Path, Any]:
    cwd = stringify(payload.get("cwd")) or os.getcwd()
    repo_root = repo_root_from_cwd(cwd)
    paths = get_paths(repo_root, scope="project" if project else "user")
    return repo_root, paths


def common_metadata(payload: dict[str, Any], repo_root: pathlib.Path, cwd: str) -> dict[str, Any]:
    return {
        "hook_event_name": payload.get("hook_event_name"),
        "session_id": payload.get("session_id"),
        "turn_id": payload.get("turn_id"),
        "cwd": cwd,
        "repo_root": str(repo_root),
        "project_name": repo_root.name,
        "git_branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"], cwd=str(repo_root)),
        "git_commit": git_value(["rev-parse", "--short", "HEAD"], cwd=str(repo_root)),
        "model": payload.get("model"),
    }


def handle_user_prompt(project: bool = False) -> int:
    payload = read_stdin_json()
    cwd = stringify(payload.get("cwd")) or os.getcwd()
    repo_root, paths = hook_paths(payload, project)
    prompt_raw = stringify(payload.get("prompt") or payload.get("user_prompt") or "")
    prompt_redacted = redact_secrets(prompt_raw)
    normalized = normalize_prompt(prompt_redacted)
    paths.history_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "id": f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{short_hash(prompt_redacted)}",
        "timestamp": utc_now(),
        "event": "UserPromptSubmit",
        **common_metadata(payload, repo_root, cwd),
        "prompt_redacted": prompt_redacted,
        "normalized_prompt": normalized,
        "prompt_hash": short_hash(normalized),
        "files_mentioned": extract_files(prompt_redacted),
        "language": "ko" if re.search(r"[가-힣]", prompt_redacted or "") else "en",
        "storage_scope": paths.scope,
        "raw_payload_keys": sorted(list(payload.keys())),
    }
    with paths.prompts_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


def handle_turn_stop(project: bool = False) -> int:
    payload = read_stdin_json()
    cwd = stringify(payload.get("cwd")) or os.getcwd()
    repo_root, paths = hook_paths(payload, project)
    paths.history_dir.mkdir(parents=True, exist_ok=True)
    changed_files = get_changed_files(repo_root)
    text = payload_text(payload)
    command = extract_command(payload)
    exit_code = extract_exit_code(payload)
    success = infer_success(payload, exit_code)
    commands_seen = [command] if command else []
    entry = {
        "id": f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-stop",
        "timestamp": utc_now(),
        "event": "Stop",
        **common_metadata(payload, repo_root, cwd),
        "changed_files": changed_files,
        "changed_file_count": len(changed_files),
        "commands_seen": commands_seen,
        "exit_codes_seen": [exit_code] if exit_code is not None else [],
        "success": success,
        "has_test_signal": bool(TEST_RE.search(command or text)),
        "test_passed": success if TEST_RE.search(command or text) else None,
        "has_lint_signal": bool(LINT_RE.search(command or text)),
        "lint_passed": success if LINT_RE.search(command or text) else None,
        "repeat_fix_signal": bool(REPEAT_FIX_RE.search(text)),
        "summary": "Codex turn stopped",
        "storage_scope": paths.scope,
        "raw_payload_keys": sorted(list(payload.keys())),
    }
    with paths.turns_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


def handle_post_tool_use(project: bool = False) -> int:
    payload = read_stdin_json()
    cwd = stringify(payload.get("cwd")) or os.getcwd()
    repo_root, paths = hook_paths(payload, project)
    paths.history_dir.mkdir(parents=True, exist_ok=True)
    command = extract_command(payload)
    exit_code = extract_exit_code(payload)
    success = infer_success(payload, exit_code)
    changed_files = get_changed_files(repo_root)
    tool_name = str(
        first_value(payload, [("tool_name",), ("tool",), ("name",), ("tool_call", "name")]) or "unknown"
    )
    entry = {
        "id": f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-tool",
        "timestamp": utc_now(),
        "event": "PostToolUse",
        **common_metadata(payload, repo_root, cwd),
        "tool_name": tool_name,
        "command": command,
        "exit_code": exit_code,
        "success": success,
        "is_test_command": bool(TEST_RE.search(command)),
        "is_lint_command": bool(LINT_RE.search(command)),
        "changed_files": changed_files,
        "changed_file_count": len(changed_files),
        "output_tail": output_tail(payload),
        "storage_scope": paths.scope,
        "raw_payload_keys": sorted(list(payload.keys())),
    }
    with paths.tool_uses_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0
