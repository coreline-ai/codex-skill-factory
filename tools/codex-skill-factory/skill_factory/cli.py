from __future__ import annotations

import json
import pathlib
from typing import Any, Optional

import typer
from jinja2 import Environment, StrictUndefined
from rich.console import Console
from rich.table import Table

from .analytics import compute_analytics
from .approvals import (
    apply_existing_statuses,
    ignore_candidate,
    set_candidate_status,
    unignore_candidate,
    utc_now,
)
from .dashboard import build_dashboard_data, render_dashboard_html
from .enrichment import enrich_candidate, enrich_candidates
from .hook_handlers import handle_post_tool_use, handle_turn_stop, handle_user_prompt
from .rules import classify_prompt, get_rule
from .similarity import build_similarity_candidates
from .storage import get_paths, read_json, read_jsonl, touch, write_json, write_text

app = typer.Typer(help="Analyze Codex prompt logs and create reusable Codex skills.")
console = Console()


def _scope(project: bool) -> str:
    return "project" if project else "user"


def resolve_paths(repo: Optional[pathlib.Path] = None, project: bool = False):
    # Backward compatibility: an explicit --repo means project-local storage.
    return get_paths(repo if (project or repo is not None) else None, scope="project" if (project or repo is not None) else "user")


def hook_command(name: str, project: bool = False) -> str:
    suffix = " --project" if project else ""
    return f"codex-skill-factory {name}{suffix}"


def build_hooks_config(project: bool = False) -> dict[str, Any]:
    return {
        "hooks": {
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command("hook-user-prompt", project=project),
                            "statusMessage": "Logging Codex prompt",
                        }
                    ]
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command("hook-turn-stop", project=project),
                            "statusMessage": "Logging Codex turn",
                        }
                    ]
                }
            ],
            "PostToolUse": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command("hook-post-tool-use", project=project),
                            "statusMessage": "Logging Codex tool use",
                        }
                    ]
                }
            ],
        }
    }


def enable_hooks_config_text(existing: str = "") -> str:
    if "codex_hooks = true" in existing:
        return existing if existing.endswith("\n") else existing + "\n"
    if "[features]" in existing:
        lines = existing.splitlines()
        out: list[str] = []
        inserted = False
        in_features = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                if in_features and not inserted:
                    out.append("codex_hooks = true")
                    inserted = True
                in_features = stripped == "[features]"
            out.append(line)
        if in_features and not inserted:
            out.append("codex_hooks = true")
        return "\n".join(out).rstrip() + "\n"
    prefix = "[features]\ncodex_hooks = true\n"
    return prefix + ("\n" + existing.strip() + "\n" if existing.strip() else "")


def ensure_product_files(repo: Optional[pathlib.Path] = None, project: bool = False, dry_run: bool = False):
    paths = resolve_paths(repo, project=project)
    config_file = paths.codex_config_dir / "config.toml"
    hooks_file = paths.codex_config_dir / "hooks.json"
    targets = [
        paths.codex_config_dir,
        paths.history_dir,
        paths.suggestions_dir,
        paths.skills_dir,
    ]
    if dry_run:
        return paths, config_file, hooks_file, targets

    for directory in targets:
        directory.mkdir(parents=True, exist_ok=True)
    for path in (paths.prompts_file, paths.turns_file, paths.tool_uses_file):
        touch(path)
    if not paths.candidates_file.exists():
        write_json(paths.candidates_file, [])
    if not paths.ignored_file.exists():
        write_json(paths.ignored_file, {"ignored": {}})
    existing_config = config_file.read_text(encoding="utf-8") if config_file.exists() else ""
    write_text(config_file, enable_hooks_config_text(existing_config))
    write_json(hooks_file, build_hooks_config(project=project))
    return paths, config_file, hooks_file, targets


def scan_candidates(
    repo: Optional[pathlib.Path] = None,
    project: bool = False,
    min_frequency: int = 2,
    include_similarity: bool = True,
    similarity_threshold: float = 0.52,
    include_enrichment: bool = True,
) -> tuple[list[dict], dict, Any]:
    paths = resolve_paths(repo, project=project)
    previous_candidates = read_json(paths.candidates_file, default=[])
    ignored = read_json(paths.ignored_file, default={"ignored": {}})
    candidates = build_candidates(
        read_jsonl(paths.prompts_file),
        min_frequency=min_frequency,
        include_similarity=include_similarity,
        similarity_threshold=similarity_threshold,
        include_enrichment=include_enrichment,
    )
    candidates = apply_existing_statuses(candidates, previous_candidates, ignored)
    write_json(paths.candidates_file, candidates)
    write_text(paths.report_file, render_report(candidates))
    analytics = build_and_write_analytics(repo, project=project)
    return candidates, analytics, paths


def render_candidate_table(candidates: list[dict], title: str = "Codex Skill Factory Inbox") -> Table:
    table = Table(title=title)
    table.add_column("Name")
    table.add_column("Score")
    table.add_column("Total")
    table.add_column("Source")
    table.add_column("Quality")
    table.add_column("Status")
    table.add_column("Next")
    for c in candidates:
        skill_spec = c.get("skill_spec") if isinstance(c.get("skill_spec"), dict) else {}
        quality = skill_spec.get("prompt_quality", {}).get("score") if skill_spec else None
        status = c.get("status", "pending_review")
        next_action = "promote" if status in {"pending_review", "approved"} else "-"
        table.add_row(
            c["name"],
            str(c.get("score", 0)),
            str(c.get("frequency_total", 0)),
            c.get("source", "rule"),
            str(quality) if quality is not None else "-",
            status,
            next_action,
        )
    return table


def build_rule_candidates(prompts: list[dict], min_frequency: int = 2) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in prompts:
        text = row.get("prompt_redacted") or row.get("prompt") or ""
        if not isinstance(text, str):
            text = str(text)
        for name in classify_prompt(text):
            grouped.setdefault(name, []).append(row)

    candidates = []
    for name, rows in grouped.items():
        rule = get_rule(name)
        if not rule or len(rows) < min_frequency:
            continue
        examples = list(
            dict.fromkeys((r.get("prompt_redacted") or "") for r in rows if r.get("prompt_redacted"))
        )[:5]
        candidates.append(
            {
                "name": rule.name,
                "title": rule.title,
                "description": rule.description,
                "score": min(100, len(rows) * 10),
                "frequency_total": len(rows),
                "example_prompts": examples,
                "when_to_use": rule.when_to_use,
                "when_not_to_use": rule.when_not_to_use,
                "goal": rule.goal,
                "workflow": rule.workflow,
                "verification": rule.verification,
                "anti_patterns": rule.anti_patterns,
                "status": "pending_review",
                "source": "rule",
            }
        )
    return sorted(candidates, key=lambda x: (-x["score"], x["name"]))


def build_candidates(
    prompts: list[dict],
    min_frequency: int = 2,
    include_similarity: bool = True,
    similarity_threshold: float = 0.52,
    include_enrichment: bool = True,
) -> list[dict]:
    candidates = build_rule_candidates(prompts, min_frequency=min_frequency)
    if include_similarity:
        existing_names = {candidate["name"] for candidate in candidates}
        candidates.extend(
            build_similarity_candidates(
                prompts,
                existing_candidate_names=existing_names,
                threshold=similarity_threshold,
                min_frequency=min_frequency,
            )
        )
    candidates = sorted(
        candidates, key=lambda x: (-int(x.get("score", 0)), x.get("source", "rule"), x["name"])
    )
    if include_enrichment:
        candidates = enrich_candidates(candidates)
    return candidates


def render_skill(
    candidate: dict,
    include_evidence: bool = False,
    include_enriched: bool = True,
) -> str:
    template_path = pathlib.Path(__file__).parent / "templates" / "SKILL.md.j2"
    env = Environment(trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined)
    template = env.from_string(template_path.read_text(encoding="utf-8"))
    skill_spec = candidate.get("skill_spec") if isinstance(candidate.get("skill_spec"), dict) else {}
    return (
        template.render(
            candidate=candidate,
            include_evidence=include_evidence,
            include_enriched=include_enriched,
            has_skill_spec=bool(skill_spec),
            skill_spec=skill_spec,
        ).rstrip()
        + "\n"
    )


def render_report(candidates: list[dict], include_ignored: bool = True) -> str:
    visible_candidates = [
        candidate
        for candidate in candidates
        if include_ignored or candidate.get("status") != "ignored"
    ]
    lines = ["# Codex Skill Suggestions", ""]
    if not visible_candidates:
        return "# Codex Skill Suggestions\n\n아직 생성할 만한 스킬 후보가 없습니다.\n"
    for idx, c in enumerate(visible_candidates, start=1):
        source = c.get("source", "rule")
        skill_spec = c.get("skill_spec") if isinstance(c.get("skill_spec"), dict) else {}
        prompt_quality = skill_spec.get("prompt_quality", {}) if skill_spec else {}
        lines += [
            f"## {idx}. `{c['name']}`",
            "",
            f"- 점수: {c['score']}",
            f"- 전체 빈도: {c['frequency_total']}",
            f"- 상태: {c.get('status', 'pending_review')}",
            f"- 출처: {source}",
        ]
        if prompt_quality:
            diagnostics = prompt_quality.get("diagnostics", [])
            lines += [
                f"- Prompt 품질 점수: {prompt_quality.get('score')}",
                f"- 주요 진단: {diagnostics[0] if diagnostics else '없음'}",
            ]
        if source == "similarity":
            similarity = c.get("similarity", {})
            lines += [
                f"- 평균 유사도: {similarity.get('average_similarity')}",
                f"- 대표 토큰: {', '.join(similarity.get('top_terms', []))}",
            ]
        lines += ["", c["description"], "", "### 예시", ""]
        lines += [f"- {p}" for p in c.get("example_prompts", [])]
        lines += [
            "",
            "### 명령",
            "",
            "```bash",
            f"codex-skill-factory preview {c['name']}",
            f"codex-skill-factory approve {c['name']}",
            f"codex-skill-factory ignore {c['name']}",
            f"codex-skill-factory create {c['name']}",
            "```",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def load_candidates(repo: Optional[pathlib.Path] = None, project: bool = False) -> list[dict]:
    return read_json(resolve_paths(repo, project=project).candidates_file, default=[])


def save_candidates(
    candidates: list[dict],
    repo: Optional[pathlib.Path] = None,
    project: bool = False,
) -> None:
    paths = resolve_paths(repo, project=project)
    write_json(paths.candidates_file, candidates)
    write_text(paths.report_file, render_report(candidates))


def find_candidate(name: str, repo: Optional[pathlib.Path] = None, project: bool = False) -> dict:
    for candidate in load_candidates(repo, project=project):
        if candidate["name"] == name:
            return candidate
    raise typer.BadParameter(f"Candidate not found: {name}")


def list_skill_names(skills_dir: pathlib.Path) -> list[str]:
    if not skills_dir.exists():
        return []
    return sorted(
        path.name
        for path in skills_dir.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    )


def build_and_write_analytics(repo: Optional[pathlib.Path] = None, project: bool = False) -> dict:
    paths = resolve_paths(repo, project=project)
    analytics = compute_analytics(
        prompts=read_jsonl(paths.prompts_file),
        turns=read_jsonl(paths.turns_file),
        tool_uses=read_jsonl(paths.tool_uses_file),
        candidates=read_json(paths.candidates_file, default=[]),
        skills=list_skill_names(paths.skills_dir),
    )
    write_json(paths.analytics_file, analytics)
    return analytics


@app.command()
def init(
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root for --project."),
    project: bool = typer.Option(False, "--project", help="Initialize project-local hooks/storage."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Run without confirmation."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show planned changes without writing files."),
) -> None:
    """Prepare Codex hooks, local storage, and skill output directories."""
    project = project or repo is not None
    paths, config_file, hooks_file, targets = ensure_product_files(repo, project=project, dry_run=dry_run)
    scope = _scope(project)
    if dry_run:
        console.print(f"[cyan]Dry run.[/cyan] Scope: {scope}")
        for directory in targets:
            console.print(f"Would create directory: {directory}")
        console.print(f"Would write config: {config_file}")
        console.print(f"Would write hooks: {hooks_file}")
        return
    if not yes:
        console.print(f"Initializing Codex Skill Factory in [bold]{scope}[/bold] scope.")
    console.print("[green]Codex Skill Factory initialized.[/green]")
    console.print(f"Scope: {scope}")
    console.print(f"Prompt history: {paths.history_dir}")
    console.print(f"Skill factory data: {paths.suggestions_dir}")
    console.print(f"Skill output: {paths.skills_dir}")
    console.print(f"Hooks: {hooks_file}")
    console.print("Run next: codex-skill-factory inbox")


@app.command()
def scan(
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root to scan."),
    min_frequency: int = typer.Option(2, "--min-frequency", min=1, help="Minimum matching prompt count."),
    similarity: bool = typer.Option(True, "--similarity/--no-similarity", help="Include semantic similarity candidates."),
    similarity_threshold: float = typer.Option(0.52, "--similarity-threshold", min=0.0, max=1.0),
    enrich: bool = typer.Option(True, "--enrich/--no-enrich", help="Add prompt contract and quality guidance."),
) -> None:
    candidates, analytics, paths = scan_candidates(
        repo=repo,
        min_frequency=min_frequency,
        include_similarity=similarity,
        similarity_threshold=similarity_threshold,
        include_enrichment=enrich,
    )
    console.print(f"[green]Scan complete.[/green] Candidates: {len(candidates)}")
    console.print(f"Report: {paths.report_file}")
    console.print(f"Analytics: {paths.analytics_file}")
    console.print(f"Command success rate: {analytics.get('commands', {}).get('success_rate')}")


@app.command()
def inbox(
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root for project scope."),
    project: bool = typer.Option(False, "--project", help="Use project-local storage."),
    no_interactive: bool = typer.Option(False, "--no-interactive", help="Do not prompt for actions."),
    include_ignored: bool = typer.Option(False, "--include-ignored", help="Show ignored candidates too."),
    min_frequency: int = typer.Option(2, "--min-frequency", min=1, help="Minimum matching prompt count."),
    similarity: bool = typer.Option(True, "--similarity/--no-similarity", help="Include similarity candidates."),
    similarity_threshold: float = typer.Option(0.52, "--similarity-threshold", min=0.0, max=1.0),
) -> None:
    """Scan prompt logs and show the candidate inbox."""
    project = project or repo is not None
    candidates, analytics, paths = scan_candidates(
        repo=repo,
        project=project,
        min_frequency=min_frequency,
        include_similarity=similarity,
        similarity_threshold=similarity_threshold,
        include_enrichment=True,
    )
    visible = [
        candidate
        for candidate in candidates
        if include_ignored or candidate.get("status") != "ignored"
    ]
    console.print(render_candidate_table(visible))
    console.print(f"Candidates: {len(visible)} / {len(candidates)}")
    console.print(f"Data: {paths.candidates_file}")
    console.print(f"Command success rate: {analytics.get('commands', {}).get('success_rate')}")
    if no_interactive or not visible:
        return
    for candidate in visible:
        action = typer.prompt(
            f"{candidate['name']} action: promote / preview / ignore / skip / quit",
            default="skip",
        ).strip().lower()
        if action in {"q", "quit"}:
            break
        if action in {"m", "p", "promote"}:
            promote(candidate["name"], repo=repo, project=project, yes=True)
        elif action in {"v", "preview"}:
            console.print(render_skill(candidate, include_evidence=True, include_enriched=True))
        elif action in {"i", "ignore"}:
            ignore_cmd(candidate["name"], repo=repo, reason="ignored from inbox")
        else:
            console.print("Skipped.")


@app.command()
def report(
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root."),
    include_ignored: bool = typer.Option(False, "--include-ignored", help="Show ignored candidates too."),
) -> None:
    candidates = [
        candidate
        for candidate in load_candidates(repo)
        if include_ignored or candidate.get("status") != "ignored"
    ]
    table = Table(title="Codex Skill Suggestions")
    table.add_column("Name")
    table.add_column("Score")
    table.add_column("Total")
    table.add_column("Source")
    table.add_column("Quality")
    table.add_column("Status")
    for c in candidates:
        skill_spec = c.get("skill_spec") if isinstance(c.get("skill_spec"), dict) else {}
        quality = skill_spec.get("prompt_quality", {}).get("score") if skill_spec else None
        table.add_row(
            c["name"],
            str(c["score"]),
            str(c["frequency_total"]),
            c.get("source", "rule"),
            str(quality) if quality is not None else "-",
            c.get("status", "pending_review"),
        )
    console.print(table)


@app.command()
def preview(
    name: str,
    evidence: bool = typer.Option(True, "--evidence/--no-evidence", help="Include example prompts."),
    enriched: bool = typer.Option(True, "--enriched/--no-enriched", help="Show prompt quality guidance."),
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root."),
) -> None:
    candidate = find_candidate(name, repo)
    if enriched and not isinstance(candidate.get("skill_spec"), dict):
        candidate = enrich_candidate(candidate)
    console.print(render_skill(candidate, include_evidence=evidence, include_enriched=enriched))


@app.command()
def approve(
    name: str,
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root."),
) -> None:
    paths = resolve_paths(repo)
    candidates = load_candidates(repo)
    ignored = unignore_candidate(read_json(paths.ignored_file, default={"ignored": {}}), name)
    if not set_candidate_status(candidates, name, "approved", approved_at=utc_now()):
        raise typer.BadParameter(f"Candidate not found: {name}")
    write_json(paths.ignored_file, ignored)
    save_candidates(candidates, repo)
    console.print(f"[green]Approved:[/green] {name}")


@app.command("ignore")
def ignore_cmd(
    name: str,
    reason: str = typer.Option("", "--reason", help="Optional ignore reason."),
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root."),
) -> None:
    paths = resolve_paths(repo)
    candidates = load_candidates(repo)
    ignored = ignore_candidate(read_json(paths.ignored_file, default={"ignored": {}}), name, reason=reason)
    if not set_candidate_status(candidates, name, "ignored", ignored=ignored.get("ignored", {}).get(name)):
        raise typer.BadParameter(f"Candidate not found: {name}")
    write_json(paths.ignored_file, ignored)
    save_candidates(candidates, repo)
    console.print(f"[yellow]Ignored:[/yellow] {name}")


@app.command()
def unignore(
    name: str,
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root."),
) -> None:
    paths = resolve_paths(repo)
    candidates = load_candidates(repo)
    ignored = unignore_candidate(read_json(paths.ignored_file, default={"ignored": {}}), name)
    if not set_candidate_status(candidates, name, "pending_review"):
        raise typer.BadParameter(f"Candidate not found: {name}")
    write_json(paths.ignored_file, ignored)
    save_candidates(candidates, repo)
    console.print(f"[green]Unignored:[/green] {name}")


@app.command()
def review(
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root."),
    limit: int = typer.Option(20, "--limit", min=1, help="Maximum candidates to review."),
) -> None:
    candidates = [candidate for candidate in load_candidates(repo) if candidate.get("status") == "pending_review"]
    if not candidates:
        console.print("No pending candidates.")
        return
    for candidate in candidates[:limit]:
        console.rule(candidate["name"])
        enriched_candidate = enrich_candidate(candidate) if not isinstance(candidate.get("skill_spec"), dict) else candidate
        console.print(render_skill(enriched_candidate, include_evidence=True, include_enriched=True))
        action = typer.prompt("Action: approve / ignore / skip / quit", default="skip").strip().lower()
        if action in {"q", "quit"}:
            break
        if action in {"a", "approve"}:
            approve(candidate["name"], repo=repo)
        elif action in {"i", "ignore"}:
            reason = typer.prompt("Reason", default="")
            ignore_cmd(candidate["name"], reason=reason, repo=repo)
        else:
            console.print("Skipped.")


@app.command("enrich")
def enrich_cmd(
    name: Optional[str] = typer.Argument(None, help="Candidate name to enrich. Omit to enrich all."),
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root."),
) -> None:
    candidates = load_candidates(repo)
    if not candidates:
        console.print("No candidates found. Run scan first.")
        return
    changed = 0
    enriched_candidates = []
    for candidate in candidates:
        if name is not None and candidate.get("name") != name:
            enriched_candidates.append(candidate)
            continue
        enriched_candidates.append(enrich_candidate(candidate))
        changed += 1
    if name is not None and changed == 0:
        raise typer.BadParameter(f"Candidate not found: {name}")
    save_candidates(enriched_candidates, repo)
    build_and_write_analytics(repo)
    console.print(f"[green]Enriched candidates:[/green] {changed}")


def create_skill_from_candidate(
    name: str,
    repo: Optional[pathlib.Path] = None,
    project: bool = False,
    overwrite: bool = False,
    evidence: bool = False,
    enriched: bool = True,
    force: bool = False,
    mark_approved: bool = False,
) -> pathlib.Path:
    paths = resolve_paths(repo, project=project)
    candidates = load_candidates(repo, project=project)
    candidate = None
    for item in candidates:
        if item.get("name") == name:
            candidate = item
            break
    if candidate is None:
        raise typer.BadParameter(f"Candidate not found: {name}")
    if candidate.get("status") == "ignored" and not force:
        raise typer.BadParameter(f"Candidate is ignored. Use --force to create anyway: {name}")
    skill_dir = paths.skills_dir / name
    skill_path = skill_dir / "SKILL.md"
    if skill_path.exists() and not overwrite:
        raise typer.BadParameter(f"Skill already exists: {skill_path}")
    if enriched and not isinstance(candidate.get("skill_spec"), dict):
        candidate.update(enrich_candidate(candidate))
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(
        render_skill(candidate, include_evidence=evidence, include_enriched=enriched),
        encoding="utf-8",
    )
    if mark_approved and candidate.get("status") == "pending_review":
        candidate["approved_at"] = utc_now()
    candidate["status"] = "created"
    candidate["created_at"] = utc_now()
    save_candidates(candidates, repo, project=project)
    build_and_write_analytics(repo, project=project)
    return skill_path


@app.command()
def create(
    name: str,
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite an existing skill."),
    evidence: bool = typer.Option(False, "--evidence/--no-evidence", help="Include example prompts."),
    enriched: bool = typer.Option(True, "--enriched/--no-enriched", help="Include prompt quality guide."),
    force: bool = typer.Option(False, "--force", help="Allow creating ignored candidates."),
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root."),
) -> None:
    skill_path = create_skill_from_candidate(
        name,
        repo=repo,
        project=repo is not None,
        overwrite=overwrite,
        evidence=evidence,
        enriched=enriched,
        force=force,
    )
    console.print(f"[green]Skill created:[/green] {skill_path}")


@app.command()
def promote(
    name: str,
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root for project scope."),
    project: bool = typer.Option(False, "--project", help="Use project-local storage."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Approve without interactive confirmation."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite an existing skill."),
    evidence: bool = typer.Option(False, "--evidence/--no-evidence", help="Include example prompts."),
    force: bool = typer.Option(False, "--force", help="Allow promoting ignored candidates."),
) -> None:
    """Approve a candidate and install it as a Codex Skill."""
    project = project or repo is not None
    candidate = find_candidate(name, repo, project=project)
    if candidate.get("status") == "ignored" and not force:
        raise typer.BadParameter(f"Candidate is ignored. Use --force to promote anyway: {name}")
    if not isinstance(candidate.get("skill_spec"), dict):
        candidate = enrich_candidate(candidate)
    if not yes:
        console.print(render_skill(candidate, include_evidence=evidence, include_enriched=True))
        if not typer.confirm(f"Promote {name} to an installed Codex Skill?"):
            raise typer.Exit(1)
    skill_path = create_skill_from_candidate(
        name,
        repo=repo,
        project=project,
        overwrite=overwrite,
        evidence=evidence,
        enriched=True,
        force=force,
        mark_approved=True,
    )
    console.print(f"[green]Skill installed:[/green] {skill_path}")


@app.command("analytics")
def analytics_cmd(repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root.")) -> None:
    paths = resolve_paths(repo)
    analytics = build_and_write_analytics(repo)
    summary = analytics.get("summary", {})
    commands = analytics.get("commands", {})
    table = Table(title="Codex Skill Factory Analytics")
    table.add_column("Metric")
    table.add_column("Value")
    for key in (
        "total_prompts",
        "total_turns",
        "total_tool_uses",
        "total_candidates",
        "generated_skills",
        "repeat_fix_requests",
        "average_changed_files",
    ):
        table.add_row(key, str(summary.get(key)))
    table.add_row("command_success_rate", str(commands.get("success_rate")))
    table.add_row("test_success_rate", str(commands.get("test_success_rate")))
    table.add_row("lint_success_rate", str(commands.get("lint_success_rate")))
    console.print(table)
    console.print(f"Analytics written: {paths.analytics_file}")


@app.command()
def dashboard(
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root."),
) -> None:
    paths = resolve_paths(repo)
    analytics = build_and_write_analytics(repo)
    candidates = read_json(paths.candidates_file, default=[])
    data = build_dashboard_data(candidates, analytics)
    write_json(paths.dashboard_data_file, data)
    write_text(paths.dashboard_file, render_dashboard_html(data))
    console.print(f"[green]Dashboard written:[/green] {paths.dashboard_file}")
    console.print("Open it in VS Code Simple Browser or your browser.")


def doctor_checks(repo: Optional[pathlib.Path] = None, project: bool = False) -> tuple[list[tuple[str, bool, str]], Any]:
    paths = resolve_paths(repo, project=project)
    config_file = paths.codex_config_dir / "config.toml"
    hooks_file = paths.codex_config_dir / "hooks.json"
    config_text = config_file.read_text(encoding="utf-8") if config_file.exists() else ""
    hooks_data = read_json(hooks_file, default={})
    hook_events = hooks_data.get("hooks", {}) if isinstance(hooks_data, dict) else {}
    checks = [
        ("Storage scope", paths.scope in {"user", "project"}, paths.scope),
        ("Codex config dir", paths.codex_config_dir.exists(), str(paths.codex_config_dir)),
        ("Codex hooks enabled", "codex_hooks = true" in config_text, str(config_file)),
        ("Codex hooks config", hooks_file.exists(), str(hooks_file)),
        ("UserPromptSubmit hook", "UserPromptSubmit" in hook_events, str(hooks_file)),
        ("Stop hook", "Stop" in hook_events, str(hooks_file)),
        ("PostToolUse hook", "PostToolUse" in hook_events, str(hooks_file)),
        ("Prompt history dir", paths.history_dir.exists(), str(paths.history_dir)),
        ("Prompts history", paths.prompts_file.exists(), str(paths.prompts_file)),
        ("Turns history", paths.turns_file.exists(), str(paths.turns_file)),
        ("Tool use history", paths.tool_uses_file.exists(), str(paths.tool_uses_file)),
        ("Skill factory data", paths.suggestions_dir.exists(), str(paths.suggestions_dir)),
        ("Candidates store", paths.candidates_file.exists(), str(paths.candidates_file)),
        ("Ignored store", paths.ignored_file.exists(), str(paths.ignored_file)),
        ("Skills dir", paths.skills_dir.exists(), str(paths.skills_dir)),
    ]
    return checks, paths


@app.command()
def doctor(
    repo: Optional[pathlib.Path] = typer.Option(None, "--repo", "-r", help="Repository root for project scope."),
    project: bool = typer.Option(False, "--project", help="Check project-local storage."),
    json_output: bool = typer.Option(False, "--json", help="Print structured JSON."),
) -> None:
    project = project or repo is not None
    checks, paths = doctor_checks(repo, project=project)
    all_ok = all(item[1] for item in checks)
    if json_output:
        print(
            json.dumps(
                {
                    "ok": all_ok,
                    "scope": paths.scope,
                    "checks": [
                        {"name": label, "ok": passed, "path": value}
                        for label, passed, value in checks
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        if not all_ok:
            raise typer.Exit(1)
        return
    table = Table(title="Codex Skill Factory Doctor")
    table.add_column("Check")
    table.add_column("OK")
    table.add_column("Path")
    for label, passed, value in checks:
        table.add_row(label, "✅" if passed else "❌", value)
    console.print(table)
    if not all_ok:
        raise typer.Exit(1)


@app.command("hook-user-prompt", hidden=True)
def hook_user_prompt(project: bool = typer.Option(False, "--project", help="Use project-local storage.")) -> None:
    raise typer.Exit(handle_user_prompt(project=project))


@app.command("hook-turn-stop", hidden=True)
def hook_turn_stop(project: bool = typer.Option(False, "--project", help="Use project-local storage.")) -> None:
    raise typer.Exit(handle_turn_stop(project=project))


@app.command("hook-post-tool-use", hidden=True)
def hook_post_tool_use(project: bool = typer.Option(False, "--project", help="Use project-local storage.")) -> None:
    raise typer.Exit(handle_post_tool_use(project=project))


if __name__ == "__main__":
    app()
