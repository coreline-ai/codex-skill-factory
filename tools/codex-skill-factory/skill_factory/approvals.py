from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


VALID_STATUSES = {"pending_review", "approved", "ignored", "created"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def candidate_index(candidates: list[dict]) -> dict[str, dict]:
    return {str(candidate.get("name")): candidate for candidate in candidates if candidate.get("name")}


def apply_existing_statuses(new_candidates: list[dict], previous_candidates: list[dict], ignored: dict[str, Any]) -> list[dict]:
    previous = candidate_index(previous_candidates)
    ignored_names = set((ignored.get("ignored") or {}).keys()) if isinstance(ignored, dict) else set()
    merged: list[dict] = []
    for candidate in new_candidates:
        name = str(candidate.get("name"))
        previous_candidate = previous.get(name, {})
        if name in ignored_names:
            candidate["status"] = "ignored"
            candidate["ignored"] = ignored.get("ignored", {}).get(name)
        elif previous_candidate.get("status") in VALID_STATUSES:
            candidate["status"] = previous_candidate["status"]
            for key in ("approved_at", "created_at", "ignored"):
                if key in previous_candidate:
                    candidate[key] = previous_candidate[key]
        merged.append(candidate)
    return merged


def set_candidate_status(candidates: list[dict], name: str, status: str, **metadata: Any) -> bool:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid candidate status: {status}")
    changed = False
    for candidate in candidates:
        if candidate.get("name") == name:
            candidate["status"] = status
            candidate.update(metadata)
            changed = True
    return changed


def ignore_candidate(ignored: dict[str, Any], name: str, reason: str | None = None) -> dict[str, Any]:
    data = ignored if isinstance(ignored, dict) else {}
    data.setdefault("ignored", {})[name] = {"reason": reason or "", "ignored_at": utc_now()}
    return data


def unignore_candidate(ignored: dict[str, Any], name: str) -> dict[str, Any]:
    data = ignored if isinstance(ignored, dict) else {}
    data.setdefault("ignored", {}).pop(name, None)
    return data
