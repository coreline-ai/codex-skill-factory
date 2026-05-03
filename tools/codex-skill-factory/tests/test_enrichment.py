from skill_factory.enrichment import enrich_candidate, enrich_candidates, is_enriched


def test_enrich_candidate_adds_skill_spec_without_mutating_original():
    candidate = {
        "name": "fix-failing-tests",
        "title": "Failing Test Fixer",
        "description": "Use when tests fail.",
        "goal": "Fix failing tests.",
        "workflow": ["reproduce", "fix", "verify"],
        "verification": ["pytest"],
        "anti_patterns": ["do not delete assertions"],
        "example_prompts": ["pytest 실패 고쳐줘"],
    }
    enriched = enrich_candidate(candidate)
    assert "skill_spec" not in candidate
    assert is_enriched(enriched)
    assert enriched["skill_spec"]["better_prompt_templates"]["minimal"]
    assert enriched["skill_spec"]["prompt_quality"]["score"] > 0


def test_enrich_candidates_handles_multiple_candidates():
    candidates = [
        {"name": "a", "description": "fix error", "verification": ["pytest"]},
        {"name": "b", "description": "update docs", "verification": []},
    ]
    enriched = enrich_candidates(candidates)
    assert len(enriched) == 2
    assert all(is_enriched(candidate) for candidate in enriched)
