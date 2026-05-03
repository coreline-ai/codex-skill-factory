from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from .rules import classify_prompt

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{1,}|[가-힣]{2,}")
_PATH_RE = re.compile(
    r"(?:[\w.\-]+/)*[\w.\-]+\.(?:py|ts|tsx|js|jsx|md|json|yaml|yml|toml|sql|html|css|go|rs|java|kt|swift|php|rb|c|cpp|h)"
)
_URL_RE = re.compile(r"https?://\S+")
_CODE_RE = re.compile(r"`[^`]+`")
_NUM_RE = re.compile(r"\b\d+\b")

_STOPWORDS = {
    "the",
    "and",
    "for",
    "this",
    "that",
    "with",
    "please",
    "need",
    "needs",
    "해줘",
    "해주세요",
    "하고",
    "현재",
    "파일",
    "코드",
    "구현",
    "수정",
    "분석",
    "검토",
    "문서",
}


@dataclass(frozen=True)
class SimilarityCluster:
    cluster_id: str
    rows: list[dict]
    average_similarity: float
    top_terms: list[str]


def prompt_text(row: dict) -> str:
    value = row.get("normalized_prompt") or row.get("prompt_redacted") or row.get("prompt") or ""
    return value if isinstance(value, str) else str(value)


def normalize_text(text: str) -> str:
    normalized = (text or "").lower().strip()
    normalized = _CODE_RE.sub(" code ", normalized)
    normalized = _URL_RE.sub(" url ", normalized)
    normalized = _PATH_RE.sub(" file ", normalized)
    normalized = _NUM_RE.sub(" num ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    tokens = [match.group(0) for match in _WORD_RE.finditer(normalized)]
    compact = re.sub(r"\s+", "", normalized)
    char_tokens: list[str] = []
    if len(compact) >= 6:
        for size in (3, 4):
            char_tokens.extend(f"char:{compact[i:i + size]}" for i in range(max(0, len(compact) - size + 1)))
    return [token for token in [*tokens, *char_tokens] if token not in _STOPWORDS]


def build_embeddings(texts: Iterable[str]) -> list[dict[str, float]]:
    tokenized = [tokenize(text) for text in texts]
    doc_count = len(tokenized)
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))

    embeddings: list[dict[str, float]] = []
    for tokens in tokenized:
        counts = Counter(tokens)
        vector: dict[str, float] = {}
        for token, count in counts.items():
            idf = math.log((1 + doc_count) / (1 + document_frequency[token])) + 1
            vector[token] = (1 + math.log(count)) * idf
        norm = math.sqrt(sum(value * value for value in vector.values()))
        if norm:
            vector = {token: value / norm for token, value in vector.items()}
        embeddings.append(vector)
    return embeddings


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def _connected_components(edges: dict[int, set[int]], count: int) -> list[list[int]]:
    seen: set[int] = set()
    components: list[list[int]] = []
    for idx in range(count):
        if idx in seen:
            continue
        stack = [idx]
        component: list[int] = []
        seen.add(idx)
        while stack:
            current = stack.pop()
            component.append(current)
            for nxt in edges[current]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        components.append(sorted(component))
    return components


def _top_terms(rows: list[dict], limit: int = 4) -> list[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        for token in tokenize(prompt_text(row)):
            if token.startswith("char:") or token in _STOPWORDS or len(token) < 2:
                continue
            counts[token] += 1
    return [token for token, _ in counts.most_common(limit)]


def find_similarity_clusters(
    prompts: list[dict],
    threshold: float = 0.52,
    min_cluster_size: int = 2,
) -> list[SimilarityCluster]:
    valid_rows = [row for row in prompts if not row.get("_invalid_json") and prompt_text(row).strip()]
    if len(valid_rows) < min_cluster_size:
        return []

    embeddings = build_embeddings(prompt_text(row) for row in valid_rows)
    edges: dict[int, set[int]] = defaultdict(set)
    for idx in range(len(valid_rows)):
        edges[idx]  # ensure singleton nodes exist
    pair_similarity: dict[tuple[int, int], float] = {}
    for i in range(len(valid_rows)):
        for j in range(i + 1, len(valid_rows)):
            similarity = cosine_similarity(embeddings[i], embeddings[j])
            pair_similarity[(i, j)] = similarity
            if similarity >= threshold:
                edges[i].add(j)
                edges[j].add(i)

    clusters: list[SimilarityCluster] = []
    for component in _connected_components(edges, len(valid_rows)):
        if len(component) < min_cluster_size:
            continue
        similarities = [
            pair_similarity[(min(i, j), max(i, j))]
            for index, i in enumerate(component)
            for j in component[index + 1 :]
            if (min(i, j), max(i, j)) in pair_similarity
        ]
        average = sum(similarities) / len(similarities) if similarities else 1.0
        rows = [valid_rows[i] for i in component]
        row_hash = hashlib.sha256("|".join(prompt_text(row) for row in rows).encode("utf-8")).hexdigest()[:8]
        clusters.append(
            SimilarityCluster(
                cluster_id=f"similar-{row_hash}",
                rows=rows,
                average_similarity=round(average, 4),
                top_terms=_top_terms(rows),
            )
        )
    return sorted(clusters, key=lambda cluster: (-len(cluster.rows), -cluster.average_similarity, cluster.cluster_id))


def _slug_terms(terms: list[str], fallback: str) -> str:
    ascii_terms = [re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-") for term in terms]
    ascii_terms = [term for term in ascii_terms if term and not term.startswith("char-")]
    if ascii_terms:
        return "-".join(ascii_terms[:3])[:48].strip("-")
    return fallback


def _representative_examples(rows: list[dict], limit: int = 5) -> list[str]:
    examples: list[str] = []
    for row in rows:
        value = row.get("prompt_redacted") or row.get("prompt") or prompt_text(row)
        if value and value not in examples:
            examples.append(str(value))
        if len(examples) >= limit:
            break
    return examples


def build_similarity_candidates(
    prompts: list[dict],
    existing_candidate_names: set[str] | None = None,
    threshold: float = 0.52,
    min_frequency: int = 2,
) -> list[dict]:
    existing_candidate_names = existing_candidate_names or set()
    candidates: list[dict] = []
    for cluster in find_similarity_clusters(prompts, threshold=threshold, min_cluster_size=min_frequency):
        matched_rule_names = {name for row in cluster.rows for name in classify_prompt(prompt_text(row))}
        if matched_rule_names and matched_rule_names.issubset(existing_candidate_names):
            continue

        slug = _slug_terms(cluster.top_terms, cluster.cluster_id)
        name = f"similar-{slug}"
        if name in existing_candidate_names:
            name = cluster.cluster_id
        title_terms = ", ".join(cluster.top_terms[:3]) or "similar prompts"
        examples = _representative_examples(cluster.rows)
        candidates.append(
            {
                "name": name,
                "title": f"Similar Prompt Cluster: {title_terms}",
                "description": (
                    "Use when the user repeatedly asks semantically similar requests represented by "
                    f"this prompt cluster ({len(cluster.rows)} examples)."
                ),
                "score": min(100, 35 + len(cluster.rows) * 8 + int(cluster.average_similarity * 20)),
                "frequency_total": len(cluster.rows),
                "example_prompts": examples,
                "when_to_use": [
                    "유사한 프롬프트가 반복되어 절차화된 Skill 후보가 필요할 때",
                    "키워드 규칙으로는 잡히지 않지만 의미상 같은 작업이 반복될 때",
                ],
                "when_not_to_use": [
                    "예시 프롬프트들이 서로 다른 목표를 갖는 경우",
                    "한 저장소나 특정 고객명에만 강하게 의존하는 경우",
                ],
                "goal": "Turn a repeated semantic prompt pattern into a reusable, verified Codex Skill.",
                "workflow": [
                    "대표 예시 프롬프트들을 검토한다.",
                    "공통 목표와 반복 절차를 추출한다.",
                    "프로젝트 고유 정보나 민감정보를 제거한다.",
                    "검증 방법과 금지 사항을 명확히 작성한다.",
                    "생성 전 사람이 후보를 승인한다.",
                ],
                "verification": [
                    "예시 프롬프트들이 같은 Skill로 처리 가능한지 확인한다.",
                    "생성된 Skill이 특정 파일/고객/비밀값에 의존하지 않는지 확인한다.",
                ],
                "anti_patterns": [
                    "유사도 점수만 보고 자동 생성하지 않는다.",
                    "서로 다른 목적의 프롬프트를 하나의 Skill로 합치지 않는다.",
                ],
                "status": "pending_review",
                "source": "similarity",
                "similarity": {
                    "cluster_id": cluster.cluster_id,
                    "average_similarity": cluster.average_similarity,
                    "threshold": threshold,
                    "top_terms": cluster.top_terms,
                },
            }
        )
    return candidates
