from skill_factory.analytics import compute_analytics


def test_compute_analytics_counts_command_success_rates():
    analytics = compute_analytics(
        prompts=[
            {"prompt_hash": "a", "prompt_redacted": "pytest 실패 고쳐줘"},
            {"prompt_hash": "a", "prompt_redacted": "pytest 실패 고쳐줘"},
            {"prompt_hash": "b", "prompt_redacted": "아직 실패해 다시 고쳐줘"},
        ],
        turns=[{"commands_seen": ["pytest tests"], "exit_code": 0, "changed_file_count": 2}],
        tool_uses=[
            {"command": "pytest tests", "exit_code": 0, "success": True},
            {"command": "ruff check .", "exit_code": 1, "success": False},
        ],
        candidates=[{"name": "fix-failing-tests", "status": "approved", "source": "rule", "score": 20}],
        skills=["fix-failing-tests"],
    )
    assert analytics["summary"]["total_prompts"] == 3
    assert analytics["summary"]["repeat_fix_requests"] == 1
    assert analytics["commands"]["success_rate"] == 0.6667
    assert analytics["commands"]["test_success_rate"] == 1.0
    assert analytics["commands"]["lint_success_rate"] == 0.0
    assert analytics["candidates"]["by_status"] == {"approved": 1}
