from skill_factory.spec_compiler import compile_skill_spec, extract_variable_slots, infer_task_archetype


def test_infer_task_archetype_for_common_candidates():
    assert infer_task_archetype({"name": "fix-failing-tests", "description": "fix pytest errors"}) == "fix"
    assert infer_task_archetype({"name": "update-docs", "description": "update README docs"}) == "document"


def test_compile_skill_spec_preserves_general_contract_shape():
    candidate = {
        "name": "fix-failing-tests",
        "title": "Failing Test Fixer",
        "description": "Use when tests fail.",
        "goal": "Fix failing tests safely.",
        "workflow": ["재현한다", "수정한다", "검증한다"],
        "verification": ["pytest 실행"],
        "anti_patterns": ["assertion 삭제 금지"],
        "example_prompts": ["tests/test_app.py pytest 실패 고쳐줘"],
    }
    spec = compile_skill_spec(candidate)
    assert spec["task_archetype"] == "fix"
    assert spec["prompt_contract"]["intent"] == "Fix failing tests safely."
    assert spec["output_contract"]["required_sections"]
    assert any(slot["name"] == "target" for slot in spec["variable_slots"])


def test_extract_variable_slots_moves_specific_files_to_target_slot():
    candidate = {"example_prompts": ["src/app.py와 README.md를 확인해줘"], "verification": []}
    slots = extract_variable_slots(candidate)
    target = next(slot for slot in slots if slot["name"] == "target")
    assert "src/app.py" in target["evidence"]
    assert target["default_placeholder"] == "[작업 대상]"
