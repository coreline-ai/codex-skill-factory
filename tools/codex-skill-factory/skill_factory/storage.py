from __future__ import annotations

import json
import os
import pathlib
from dataclasses import dataclass
from typing import Any

Scope = str


@dataclass(frozen=True)
class Paths:
    repo_root: pathlib.Path
    scope: Scope
    codex_config_dir: pathlib.Path
    history_dir: pathlib.Path
    suggestions_dir: pathlib.Path
    prompts_file: pathlib.Path
    turns_file: pathlib.Path
    tool_uses_file: pathlib.Path
    candidates_file: pathlib.Path
    report_file: pathlib.Path
    ignored_file: pathlib.Path
    analytics_file: pathlib.Path
    dashboard_file: pathlib.Path
    dashboard_data_file: pathlib.Path
    skills_dir: pathlib.Path


def find_repo_root(start: pathlib.Path | None = None) -> pathlib.Path:
    current = (start or pathlib.Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / ".git").exists() or (path / ".codex").exists():
            return path
    return current


def get_codex_home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("CODEX_HOME") or (pathlib.Path.home() / ".codex")).expanduser().resolve()


def get_paths(repo_root: pathlib.Path | None = None, scope: Scope = "project") -> Paths:
    if scope not in {"project", "user"}:
        raise ValueError(f"Invalid scope: {scope}")
    root = repo_root.resolve() if repo_root is not None else find_repo_root()
    if scope == "user" and repo_root is None:
        root = find_repo_root()

    if scope == "user":
        codex_home = get_codex_home()
        config_dir = codex_home
        history_dir = codex_home / "prompt-history"
        suggestions_dir = codex_home / "skill-factory"
        skills_dir = codex_home / "skills"
    else:
        config_dir = root / ".codex"
        history_dir = root / ".codex-prompt-history"
        suggestions_dir = root / ".codex-skill-suggestions"
        skills_dir = root / ".codex" / "skills"

    return Paths(
        repo_root=root,
        scope=scope,
        codex_config_dir=config_dir,
        history_dir=history_dir,
        suggestions_dir=suggestions_dir,
        prompts_file=history_dir / "prompts.jsonl",
        turns_file=history_dir / "turns.jsonl",
        tool_uses_file=history_dir / "tool_uses.jsonl",
        candidates_file=suggestions_dir / "candidates.json",
        report_file=suggestions_dir / "report.md",
        ignored_file=suggestions_dir / "ignored.json",
        analytics_file=suggestions_dir / "analytics.json",
        dashboard_file=suggestions_dir / "dashboard.html",
        dashboard_data_file=suggestions_dir / "dashboard.json",
        skills_dir=skills_dir,
    )


def read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                rows.append({"_invalid_json": True, "_line_no": line_no, "_raw": line})
                continue
            rows.append(
                value
                if isinstance(value, dict)
                else {"_invalid_json": True, "_line_no": line_no, "_raw": value}
            )
    return rows


def write_json(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: pathlib.Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def touch(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
