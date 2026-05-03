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
