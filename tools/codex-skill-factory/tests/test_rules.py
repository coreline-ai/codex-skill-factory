from skill_factory.rules import classify_prompt, get_rule


def test_classify_prompt_matches_korean_and_english_keywords():
    assert "fix-failing-tests" in classify_prompt("pytest 테스트 실패 고쳐줘")
    assert "review-current-diff" in classify_prompt("please review diff before merge")


def test_classify_prompt_returns_empty_for_unknown_request():
    assert classify_prompt("오늘 점심 메뉴 추천") == []


def test_get_rule_returns_rule_by_name():
    rule = get_rule("update-docs")
    assert rule is not None
    assert rule.name == "update-docs"
