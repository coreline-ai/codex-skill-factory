from skill_factory.quality import compute_quality, enrich_quality, generate_prompt_templates
from skill_factory.spec_compiler import compile_skill_spec


def test_quality_detects_missing_verification():
    candidate = {
        "name": "sample",
        "description": "analyze something",
        "example_prompts": ["이거 분석해줘"],
        "workflow": ["분석한다"],
        "verification": [],
    }
    spec = compile_skill_spec(candidate)
    quality = compute_quality(candidate, spec)
    assert quality["dimensions"]["verification_strength"] < 70
    assert any("검증" in item for item in quality["diagnostics"])


def test_prompt_templates_are_generic_and_slot_based():
    candidate = {
        "name": "review-current-diff",
        "description": "review changes",
        "goal": "Review current changes safely.",
        "verification": ["diff 근거 확인"],
    }
    spec = compile_skill_spec(candidate)
    templates = generate_prompt_templates(spec)
    assert "[작업 대상]" in templates["minimal"]
    assert "[수정 범위와 금지사항]" in templates["high_signal"]


def test_enrich_quality_adds_questions_and_checklist():
    candidate = {"name": "sample", "description": "create output", "verification": []}
    spec = compile_skill_spec(candidate)
    enriched = enrich_quality(candidate, spec)
    assert enriched["better_prompt_templates"]["high_signal"]
    assert enriched["clarifying_questions"]
    assert enriched["quality_checklist"]
