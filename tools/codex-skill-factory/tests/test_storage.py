import json

from skill_factory.storage import get_paths, read_json, read_jsonl, write_json, write_text


def test_get_paths_uses_expected_project_directories(tmp_path):
    paths = get_paths(tmp_path)
    assert paths.scope == "project"
    assert paths.history_dir == tmp_path / ".codex-prompt-history"
    assert paths.suggestions_dir == tmp_path / ".codex-skill-suggestions"
    assert paths.skills_dir == tmp_path / ".codex" / "skills"


def test_get_paths_uses_user_scope_when_requested(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / ".codex-home"))
    paths = get_paths(tmp_path, scope="user")
    assert paths.scope == "user"
    assert paths.history_dir == tmp_path / ".codex-home" / "prompt-history"
    assert paths.suggestions_dir == tmp_path / ".codex-home" / "skill-factory"
    assert paths.skills_dir == tmp_path / ".codex-home" / "skills"


def test_read_write_json_round_trip(tmp_path):
    path = tmp_path / "nested" / "data.json"
    write_json(path, {"name": "sample", "count": 2})
    assert read_json(path, default={}) == {"name": "sample", "count": 2}


def test_read_json_returns_default_for_invalid_json(tmp_path):
    path = tmp_path / "broken.json"
    write_text(path, "not-json")
    assert read_json(path, default=[]) == []


def test_read_jsonl_keeps_invalid_lines_as_diagnostics(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text(json.dumps({"ok": True}) + "\nnot-json\n", encoding="utf-8")
    rows = read_jsonl(path)
    assert rows[0] == {"ok": True}
    assert rows[1]["_invalid_json"] is True
    assert rows[1]["_line_no"] == 2
