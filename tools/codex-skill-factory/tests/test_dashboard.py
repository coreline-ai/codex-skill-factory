from skill_factory.dashboard import build_dashboard_data, render_dashboard_html


def test_dashboard_html_contains_candidates_and_metrics():
    data = build_dashboard_data(
        candidates=[
            {
                "name": "sample-skill",
                "status": "pending_review",
                "score": 50,
                "frequency_total": 3,
                "skill_spec": {
                    "prompt_quality": {
                        "score": 81,
                        "diagnostics": ["충분합니다."],
                        "install_readiness": {
                            "grade": "review_recommended",
                            "recommendation": "확인 후 promote하세요.",
                            "blockers": [],
                        },
                    },
                    "better_prompt_templates": {"minimal": "짧은 프롬프트", "high_signal": "좋은 프롬프트"},
                },
            }
        ],
        analytics={"summary": {"total_prompts": 3, "total_candidates": 1}, "commands": {}, "repetition": {}},
    )
    html = render_dashboard_html(data)
    assert "Codex Skill Factory Dashboard" in html
    assert "sample-skill" in html
    assert "Prompt Quality" in html
    assert "Install Readiness" in html
    assert "review_recommended" in html
    assert "좋은 프롬프트" in html
    assert "codex-skill-factory promote sample-skill --repo . --yes" in html
