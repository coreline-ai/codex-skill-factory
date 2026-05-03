import json

from typer.testing import CliRunner

from skill_factory.cli import app, build_candidates, render_report, render_skill


runner = CliRunner()


def sample_prompts():
    return [
        {"prompt_redacted": "pytest 테스트 실패 고쳐줘"},
        {"prompt_redacted": "failing test in pytest needs fix"},
        {"prompt_redacted": "README 문서 업데이트"},
    ]


def test_build_candidates_applies_frequency_threshold():
    candidates = build_candidates(sample_prompts())
    assert [c["name"] for c in candidates] == ["fix-failing-tests"]
    assert candidates[0]["frequency_total"] == 2
    assert candidates[0]["score"] == 20


def test_render_skill_can_include_evidence():
    candidate = build_candidates(sample_prompts())[0]
    rendered = render_skill(candidate, include_evidence=True)
    assert "# Failing Test Fixer" in rendered
    assert "## Evidence" in rendered
    assert "pytest 테스트 실패" in rendered


def test_render_report_empty_message():
    assert "아직 생성할 만한 스킬 후보가 없습니다." in render_report([])


def test_scan_and_create_commands_use_repo_option(tmp_path):
    history_dir = tmp_path / ".codex-prompt-history"
    skills_dir = tmp_path / ".codex" / "skills"
    history_dir.mkdir(parents=True)
    skills_dir.mkdir(parents=True)
    rows = sample_prompts()
    (history_dir / "prompts.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )

    scan_result = runner.invoke(app, ["scan", "--repo", str(tmp_path)])
    assert scan_result.exit_code == 0, scan_result.output
    candidates_path = tmp_path / ".codex-skill-suggestions" / "candidates.json"
    assert candidates_path.exists()
    assert json.loads(candidates_path.read_text(encoding="utf-8"))[0]["name"] == "fix-failing-tests"

    create_result = runner.invoke(app, ["create", "fix-failing-tests", "--repo", str(tmp_path)])
    assert create_result.exit_code == 0, create_result.output
    skill_path = tmp_path / ".codex" / "skills" / "fix-failing-tests" / "SKILL.md"
    assert skill_path.exists()
    assert "# Failing Test Fixer" in skill_path.read_text(encoding="utf-8")


def test_approve_ignore_unignore_and_dashboard_commands(tmp_path):
    history_dir = tmp_path / ".codex-prompt-history"
    skills_dir = tmp_path / ".codex" / "skills"
    history_dir.mkdir(parents=True)
    skills_dir.mkdir(parents=True)
    rows = sample_prompts()
    (history_dir / "prompts.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    (history_dir / "tool_uses.jsonl").write_text(
        json.dumps({"command": "pytest tests", "exit_code": 0, "success": True}) + "\n",
        encoding="utf-8",
    )

    assert runner.invoke(app, ["scan", "--repo", str(tmp_path)]).exit_code == 0
    assert runner.invoke(app, ["approve", "fix-failing-tests", "--repo", str(tmp_path)]).exit_code == 0
    candidates = json.loads((tmp_path / ".codex-skill-suggestions" / "candidates.json").read_text())
    assert candidates[0]["status"] == "approved"

    assert runner.invoke(app, ["ignore", "fix-failing-tests", "--repo", str(tmp_path), "--reason", "duplicate"]).exit_code == 0
    candidates = json.loads((tmp_path / ".codex-skill-suggestions" / "candidates.json").read_text())
    assert candidates[0]["status"] == "ignored"

    assert runner.invoke(app, ["unignore", "fix-failing-tests", "--repo", str(tmp_path)]).exit_code == 0
    assert runner.invoke(app, ["analytics", "--repo", str(tmp_path)]).exit_code == 0
    assert runner.invoke(app, ["dashboard", "--repo", str(tmp_path)]).exit_code == 0
    assert (tmp_path / ".codex-skill-suggestions" / "dashboard.html").exists()
    assert (tmp_path / ".codex-skill-suggestions" / "dashboard.json").exists()


def test_scan_enrich_preview_and_create_include_prompt_quality(tmp_path):
    history_dir = tmp_path / ".codex-prompt-history"
    skills_dir = tmp_path / ".codex" / "skills"
    history_dir.mkdir(parents=True)
    skills_dir.mkdir(parents=True)
    rows = sample_prompts()
    (history_dir / "prompts.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )

    scan_result = runner.invoke(app, ["scan", "--repo", str(tmp_path), "--enrich"])
    assert scan_result.exit_code == 0, scan_result.output
    candidates_path = tmp_path / ".codex-skill-suggestions" / "candidates.json"
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    assert candidates[0]["skill_spec"]["prompt_quality"]["score"] > 0

    enrich_result = runner.invoke(app, ["enrich", "fix-failing-tests", "--repo", str(tmp_path)])
    assert enrich_result.exit_code == 0, enrich_result.output

    preview_result = runner.invoke(app, ["preview", "fix-failing-tests", "--repo", str(tmp_path)])
    assert preview_result.exit_code == 0, preview_result.output
    assert "Prompt quality guide" in preview_result.output
    assert "Better prompt templates" in preview_result.output

    legacy_preview = runner.invoke(
        app, ["preview", "fix-failing-tests", "--repo", str(tmp_path), "--no-enriched"]
    )
    assert legacy_preview.exit_code == 0, legacy_preview.output
    assert "Prompt quality guide" not in legacy_preview.output

    create_result = runner.invoke(app, ["create", "fix-failing-tests", "--repo", str(tmp_path)])
    assert create_result.exit_code == 0, create_result.output
    skill_text = (tmp_path / ".codex" / "skills" / "fix-failing-tests" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "## Prompt quality guide" in skill_text


def test_product_golden_path_project_scope(tmp_path):
    init_result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--yes"])
    assert init_result.exit_code == 0, init_result.output
    assert (tmp_path / ".codex" / "config.toml").exists()
    hooks = json.loads((tmp_path / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    assert "hook-user-prompt --project" in json.dumps(hooks)

    payload = {"cwd": str(tmp_path), "prompt": "pytest 테스트 실패 고쳐줘 api_key=SECRET123"}
    hook_result = runner.invoke(app, ["hook-user-prompt", "--project"], input=json.dumps(payload))
    assert hook_result.exit_code == 0, hook_result.output
    hook_result = runner.invoke(
        app,
        ["hook-user-prompt", "--project"],
        input=json.dumps({"cwd": str(tmp_path), "prompt": "failing test in pytest needs fix"}),
    )
    assert hook_result.exit_code == 0, hook_result.output

    prompt_log = (tmp_path / ".codex-prompt-history" / "prompts.jsonl").read_text(encoding="utf-8")
    assert "[REDACTED_SECRET]" in prompt_log
    assert "SECRET123" not in prompt_log

    inbox_result = runner.invoke(app, ["inbox", "--repo", str(tmp_path), "--no-interactive"])
    assert inbox_result.exit_code == 0, inbox_result.output
    candidates = json.loads(
        (tmp_path / ".codex-skill-suggestions" / "candidates.json").read_text(encoding="utf-8")
    )
    assert candidates[0]["name"] == "fix-failing-tests"

    promote_result = runner.invoke(
        app,
        ["promote", "fix-failing-tests", "--repo", str(tmp_path), "--yes"],
    )
    assert promote_result.exit_code == 0, promote_result.output
    skill_path = tmp_path / ".codex" / "skills" / "fix-failing-tests" / "SKILL.md"
    assert skill_path.exists()
    assert "Prompt quality guide" in skill_path.read_text(encoding="utf-8")

    doctor_result = runner.invoke(app, ["doctor", "--repo", str(tmp_path)])
    assert doctor_result.exit_code == 0, doctor_result.output


def test_doctor_returns_nonzero_when_not_initialized(tmp_path):
    result = runner.invoke(app, ["doctor", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "❌" in result.output
