from __future__ import annotations

import html
import json
from typing import Any


def build_dashboard_data(candidates: list[dict], analytics: dict[str, Any]) -> dict[str, Any]:
    return {
        "analytics": analytics,
        "candidates": candidates,
        "commands": {
            "inbox": "codex-skill-factory inbox --repo . --no-interactive",
            "promote": "codex-skill-factory promote <candidate> --repo . --yes",
            "analytics": "codex-skill-factory analytics --repo .",
            "dashboard": "codex-skill-factory dashboard --repo .",
        },
    }


def render_dashboard_html(data: dict[str, Any]) -> str:
    analytics = data.get("analytics", {})
    summary = analytics.get("summary", {})
    commands = analytics.get("commands", {})
    candidates = data.get("candidates", [])
    repeated = analytics.get("repetition", {}).get("top_repeated_prompts", [])
    payload = html.escape(json.dumps(data, ensure_ascii=False, indent=2))

    def card(label: str, value: Any) -> str:
        return f"<div class='metric'><span>{html.escape(label)}</span><strong>{html.escape(str(value))}</strong></div>"

    candidate_cards = []
    for candidate in candidates:
        name = str(candidate.get("name", ""))
        status = str(candidate.get("status", "pending_review"))
        source = str(candidate.get("source", "rule"))
        examples = candidate.get("example_prompts") or []
        example_html = "".join(f"<li>{html.escape(str(example))}</li>" for example in examples[:3])
        skill_spec = candidate.get("skill_spec") if isinstance(candidate.get("skill_spec"), dict) else {}
        quality = skill_spec.get("prompt_quality", {}) if skill_spec else {}
        diagnostics = quality.get("diagnostics", []) if quality else []
        templates = skill_spec.get("better_prompt_templates", {}) if skill_spec else {}
        diagnostics_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in diagnostics[:3])
        prompt_html = ""
        if templates:
            prompt_html = (
                "<details><summary>Better prompt templates</summary>"
                f"<p><b>Minimal</b></p><pre>{html.escape(str(templates.get('minimal', '')))}</pre>"
                f"<p><b>High-signal</b></p><pre>{html.escape(str(templates.get('high_signal', '')))}</pre>"
                "</details>"
            )
        candidate_cards.append(
            "<article class='candidate'>"
            f"<div><h3>{html.escape(name)}</h3><span class='pill {html.escape(status)}'>{html.escape(status)}</span>"
            f"<span class='pill'>{html.escape(source)}</span></div>"
            f"<p>{html.escape(str(candidate.get('description', '')))}</p>"
            f"<p><b>Score</b> {html.escape(str(candidate.get('score', 0)))} · "
            f"<b>Frequency</b> {html.escape(str(candidate.get('frequency_total', 0)))} · "
            f"<b>Prompt Quality</b> {html.escape(str(quality.get('score', '-')))}</p>"
            f"<ul>{example_html}</ul>"
            f"<ul class='diagnostics'>{diagnostics_html}</ul>"
            f"{prompt_html}"
            "<div class='commands'>"
            f"<code>codex-skill-factory promote {html.escape(name)} --repo . --yes</code>"
            f"<code>codex-skill-factory preview {html.escape(name)} --repo .</code>"
            f"<code>codex-skill-factory ignore {html.escape(name)} --repo .</code>"
            "</div>"
            "</article>"
        )

    repeated_rows = "".join(
        f"<tr><td>{html.escape(str(item.get('count')))}</td><td>{html.escape(str((item.get('examples') or [''])[0]))}</td></tr>"
        for item in repeated
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Codex Skill Factory Dashboard</title>
<style>
:root {{ color-scheme: light dark; --bg: #0f172a; --panel: #111827; --text: #e5e7eb; --muted: #94a3b8; --line: #334155; --brand: #38bdf8; }}
body {{ margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
main {{ max-width: 1180px; margin: 0 auto; padding: 32px; }}
h1 {{ margin: 0 0 8px; font-size: 34px; }}
section {{ margin-top: 28px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }}
.metric, .candidate, .panel {{ background: rgba(17, 24, 39, .88); border: 1px solid var(--line); border-radius: 16px; padding: 16px; box-shadow: 0 16px 40px rgba(0,0,0,.18); }}
.metric span {{ display: block; color: var(--muted); font-size: 13px; }}
.metric strong {{ display: block; margin-top: 8px; font-size: 26px; }}
.candidates {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }}
.candidate h3 {{ margin: 0 0 8px; }}
.pill {{ display: inline-block; margin: 0 6px 8px 0; padding: 3px 8px; border: 1px solid var(--line); border-radius: 999px; color: var(--muted); font-size: 12px; }}
.pill.approved {{ color: #86efac; border-color: #166534; }} .pill.ignored {{ color: #fca5a5; border-color: #7f1d1d; }} .pill.created {{ color: #93c5fd; border-color: #1d4ed8; }}
.commands {{ display: grid; gap: 8px; margin-top: 12px; }}
details {{ margin: 12px 0; }} summary {{ cursor: pointer; color: var(--brand); }}
.diagnostics {{ color: #fbbf24; }}
code, pre {{ background: #020617; border: 1px solid var(--line); border-radius: 8px; color: #bae6fd; }}
code {{ padding: 6px 8px; overflow-wrap: anywhere; }} pre {{ padding: 16px; overflow: auto; max-height: 360px; }}
table {{ width: 100%; border-collapse: collapse; }} td, th {{ border-bottom: 1px solid var(--line); padding: 10px; text-align: left; }}
.muted {{ color: var(--muted); }}
</style>
</head>
<body>
<main>
  <h1>Codex Skill Factory Dashboard</h1>
  <p class="muted">VS Code Simple Browser 또는 브라우저에서 열어 후보, 반복 요청, 성공률 신호를 검토합니다. 승인/무시는 아래 CLI 명령을 터미널에서 실행하세요.</p>

  <section class="grid">
    {card('Prompts', summary.get('total_prompts', 0))}
    {card('Candidates', summary.get('total_candidates', 0))}
    {card('Generated Skills', summary.get('generated_skills', 0))}
    {card('Tool Uses', summary.get('total_tool_uses', 0))}
    {card('Command Success', commands.get('success_rate'))}
    {card('Test Success', commands.get('test_success_rate'))}
    {card('Lint Success', commands.get('lint_success_rate'))}
    {card('Repeat Fix Requests', summary.get('repeat_fix_requests', 0))}
  </section>

  <section class="panel">
    <h2>VS Code Tasks</h2>
    <div class="commands">
      <code>Tasks: Run Task → Codex Skill Factory: Inbox</code>
      <code>Tasks: Run Task → Codex Skill Factory: Dashboard</code>
      <code>Open .codex-skill-suggestions/dashboard.html with Simple Browser</code>
    </div>
  </section>

  <section>
    <h2>Skill Candidates</h2>
    <div class="candidates">{''.join(candidate_cards) or '<p class="muted">No candidates yet.</p>'}</div>
  </section>

  <section class="panel">
    <h2>Repeated Prompts TOP 10</h2>
    <table><thead><tr><th>Count</th><th>Example</th></tr></thead><tbody>{repeated_rows}</tbody></table>
  </section>

  <section class="panel">
    <h2>Raw Dashboard Data</h2>
    <pre>{payload}</pre>
  </section>
</main>
</body>
</html>
"""
