import json
import pathlib

from typer.testing import CliRunner

from skill_factory.cli import app, build_candidates, render_report, render_skill
from skill_factory.enrichment import enrich_candidate


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


def test_render_skill_uses_archetype_output_contract_when_enriched():
    candidate = enrich_candidate(
        {
            "name": "generate-release-notes",
            "title": "Release Notes Generator",
            "description": "Use when generating release notes from changes.",
            "goal": "Generate release notes from git changes.",
            "frequency_total": 2,
            "score": 70,
            "example_prompts": ["generate release notes for the latest diff"],
            "when_to_use": ["release notes 작성이 필요할 때"],
            "when_not_to_use": ["변경 근거가 없을 때"],
            "workflow": ["변경사항을 확인한다", "릴리즈 노트를 작성한다"],
            "verification": ["diff 근거 확인"],
            "anti_patterns": ["확인되지 않은 버전 작성 금지"],
            "output_sections": [
                "Release summary",
                "Notable changes",
                "Breaking changes or migrations",
                "Validation",
                "Risks or follow-ups",
            ],
            "status": "pending_review",
            "source": "similarity",
        }
    )
    rendered = render_skill(candidate, include_evidence=False, include_enriched=True)
    output_section = rendered.split("## Output format", 1)[1].split("## Prompt quality guide", 1)[0]
    assert "- Release summary" in output_section
    assert "- Breaking changes or migrations" in output_section
    assert "- Files touched" not in output_section
    assert "## Install readiness" in rendered


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


def test_init_merges_existing_hooks_and_backs_up(tmp_path):
    codex_dir = tmp_path / ".codex"
    codex_dir.mkdir()
    hooks_file = codex_dir / "hooks.json"
    hooks_file.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {"hooks": [{"type": "command", "command": "custom-prompt-hook"}]}
                    ],
                    "PreToolUse": [
                        {"hooks": [{"type": "command", "command": "custom-pre-tool-hook"}]}
                    ],
                },
                "custom_top_level": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    init_result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--yes"])
    assert init_result.exit_code == 0, init_result.output
    hooks = json.loads(hooks_file.read_text(encoding="utf-8"))
    serialized = json.dumps(hooks, ensure_ascii=False)
    assert hooks["custom_top_level"] is True
    assert "custom-prompt-hook" in serialized
    assert "custom-pre-tool-hook" in serialized
    assert "codex-skill-factory hook-user-prompt --project" in serialized
    assert (codex_dir / "hooks.json.bak").exists()

    second_init = runner.invoke(app, ["init", "--repo", str(tmp_path), "--yes"])
    assert second_init.exit_code == 0, second_init.output
    hooks_after_second_init = json.loads(hooks_file.read_text(encoding="utf-8"))
    serialized_after_second_init = json.dumps(hooks_after_second_init, ensure_ascii=False)
    assert serialized_after_second_init.count("codex-skill-factory hook-user-prompt --project") == 1


def test_inbox_auto_non_interactive_when_stdin_is_not_tty(tmp_path):
    history_dir = tmp_path / ".codex-prompt-history"
    skills_dir = tmp_path / ".codex" / "skills"
    history_dir.mkdir(parents=True)
    skills_dir.mkdir(parents=True)
    (history_dir / "prompts.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in sample_prompts()),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["inbox", "--repo", str(tmp_path)])
    assert result.exit_code == 0, result.output
    candidates = json.loads(
        (tmp_path / ".codex-skill-suggestions" / "candidates.json").read_text(encoding="utf-8")
    )
    assert candidates[0]["name"] == "fix-failing-tests"


def test_hook_logs_redact_secrets_for_turns_and_tool_uses(tmp_path):
    assert runner.invoke(app, ["init", "--repo", str(tmp_path), "--yes"]).exit_code == 0

    stop_payload = {
        "cwd": str(tmp_path),
        "command": "pytest tests api_key=SECRET123",
        "exit_code": 0,
    }
    stop_result = runner.invoke(
        app,
        ["hook-turn-stop", "--project"],
        input=json.dumps(stop_payload),
    )
    assert stop_result.exit_code == 0, stop_result.output
    turns_text = (tmp_path / ".codex-prompt-history" / "turns.jsonl").read_text(encoding="utf-8")
    assert "[REDACTED_SECRET]" in turns_text
    assert "SECRET123" not in turns_text

    tool_payload = {
        "cwd": str(tmp_path),
        "command": "pytest tests",
        "exit_code": 1,
        "output": "FAILED password=SECRET123",
    }
    tool_result = runner.invoke(
        app,
        ["hook-post-tool-use", "--project"],
        input=json.dumps(tool_payload),
    )
    assert tool_result.exit_code == 0, tool_result.output
    tool_text = (tmp_path / ".codex-prompt-history" / "tool_uses.jsonl").read_text(
        encoding="utf-8"
    )
    assert "[REDACTED_SECRET]" in tool_text
    assert "SECRET123" not in tool_text


def test_legacy_hook_scripts_delegate_to_cli_handlers():
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    expected = {
        "log_user_prompt.py": "codex-skill-factory\", \"hook-user-prompt\", \"--project",
        "log_turn_stop.py": "codex-skill-factory\", \"hook-turn-stop\", \"--project",
        "log_post_tool_use.py": "codex-skill-factory\", \"hook-post-tool-use\", \"--project",
    }
    for filename, command_snippet in expected.items():
        text = (repo_root / ".codex" / "hooks" / filename).read_text(encoding="utf-8")
        assert command_snippet in text
        assert "SECRET_PATTERNS" not in text
        assert "jsonl" not in text


def test_doctor_returns_nonzero_when_not_initialized(tmp_path):
    result = runner.invoke(app, ["doctor", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "❌" in result.output
