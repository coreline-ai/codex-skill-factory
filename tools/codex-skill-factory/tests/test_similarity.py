from skill_factory.similarity import build_similarity_candidates, find_similarity_clusters


def test_similarity_clusters_group_related_non_rule_prompts():
    prompts = [
        {"prompt_redacted": "make a release note from current git changes"},
        {"prompt_redacted": "generate release notes for the latest diff"},
        {"prompt_redacted": "create a changelog summary from commits"},
        {"prompt_redacted": "draw a spaceship icon"},
    ]
    clusters = find_similarity_clusters(prompts, threshold=0.12, min_cluster_size=2)
    assert clusters
    assert any(len(cluster.rows) >= 2 for cluster in clusters)


def test_similarity_candidates_have_skill_shape():
    prompts = [
        {"prompt_redacted": "make release notes from current git changes"},
        {"prompt_redacted": "generate release notes for the latest diff"},
    ]
    candidates = build_similarity_candidates(prompts, threshold=0.12, min_frequency=2)
    assert candidates
    assert candidates[0]["source"] == "similarity"
    assert candidates[0]["status"] == "pending_review"
    assert candidates[0]["similarity"]["average_similarity"] > 0


def test_similarity_candidates_infer_concrete_release_notes_skill():
    prompts = [
        {"prompt_redacted": "make release notes from current git changes"},
        {"prompt_redacted": "generate release notes for the latest diff"},
        {"prompt_redacted": "write 릴리즈 노트 using commits and PR list"},
    ]
    candidates = build_similarity_candidates(prompts, threshold=0.12, min_frequency=2)
    candidate = candidates[0]
    assert candidate["name"] == "generate-release-notes"
    assert candidate["title"] == "Release Notes Generator"
    assert "Turn a repeated semantic prompt pattern" not in candidate["goal"]
    assert "release notes from commits" in candidate["goal"]
    assert any("commit range" in step or "diff" in step for step in candidate["workflow"])
    assert candidate["similarity"]["intent_profile"]["domain"] == "release-notes"


def test_similarity_candidates_keep_safe_unknown_fallback():
    prompts = [
        {"prompt_redacted": "calibrate frobnicator output with alpha knobs"},
        {"prompt_redacted": "adjust frobnicator output using beta knobs"},
    ]
    candidates = build_similarity_candidates(prompts, threshold=0.12, min_frequency=2)
    candidate = candidates[0]
    assert candidate["source"] == "similarity"
    assert candidate["name"].startswith(("handle-", "generate-", "update-", "analyze-"))
    assert "Codex Skill" not in candidate["goal"]
    assert candidate["workflow"]


def test_similarity_candidates_merge_same_intent_clusters():
    prompts = [
        {"prompt_redacted": "prepare release notes from current commits"},
        {"prompt_redacted": "prepare release notes from current commits"},
        {"prompt_redacted": "generate release summary from git commits"},
        {"prompt_redacted": "generate release summary from git commits"},
    ]
    candidates = build_similarity_candidates(prompts, threshold=0.52, min_frequency=2)
    release_candidates = [candidate for candidate in candidates if candidate["name"] == "generate-release-notes"]
    assert len(release_candidates) == 1
    assert release_candidates[0]["frequency_total"] == 4
    assert release_candidates[0]["similarity"]["merged_cluster_count"] == 2
