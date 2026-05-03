# 🧩 Skill 생성 공용 사양 (Skill Template Spec)

> **이 문서가 정의하는 것:** Codex Prompt Skill Factory가 `promote` / `create` 시점에 만들어내는 모든 `SKILL.md`에 공통으로 들어가는 구조·항목·기본값을 한곳에 모은 단일 진실 소스(Single Source of Truth).
>
> 실제 렌더링 코드와 1:1 대응합니다. 코드를 바꾸면 이 문서를 함께 갱신해야 합니다.

| 출처 모듈 | 책임 | 본 문서 대응 섹션 |
|---|---|---|
| [`templates/SKILL.md.j2`](../tools/codex-skill-factory/skill_factory/templates/SKILL.md.j2) | Skill 본문 섹션 골격 | §2, §4 |
| [`spec_compiler.py`](../tools/codex-skill-factory/skill_factory/spec_compiler.py) | task archetype, 변수 슬롯, prompt contract, 리스크 제어 | §3, §5, §6, §7 |
| [`quality.py`](../tools/codex-skill-factory/skill_factory/quality.py) | 더 나은 프롬프트 템플릿, 확인 질문, 품질 체크리스트, 일반화 노트, 7차원 점수 | §4.B, §8 |
| [`rules.py`](../tools/codex-skill-factory/skill_factory/rules.py) | 사전 정의 룰 5종의 when/workflow/anti-pattern 데이터 | §9 |

---

## 1. 렌더 진입점

| 시점 | CLI 명령 | 함수 | 옵션 |
|---|---|---|---|
| 미리보기 | `preview <name>` | `cli.render_skill` | `--evidence/--no-evidence`, `--enriched/--no-enriched` |
| 승인 후 설치 | `promote <name>` | `cli.create_skill_from_candidate` (always `enriched=True`) | `--evidence`, `--overwrite`, `--force` |
| 단독 생성 | `create <name>` | 동일 | 동일 |

기본값: `enriched=True`, `evidence=False`. 결과 파일 경로는 `<skills_dir>/<name>/SKILL.md`.

---

## 2. 항상 들어가는 섹션 (Base)

> 후보(candidate)가 어떤 source(rule / similarity)에서 왔든 동일하게 적용됩니다.

### 2.1 Frontmatter

```yaml
---
name: <slug>           # 후보 name. Codex가 Skill 식별자로 사용
description: <one-line># Codex가 trigger 판단에 쓰는 한 줄 트리거 문구
---
```

### 2.2 본문 고정 섹션 순서

| # | 섹션 | 데이터 출처 | 형식 |
|---|---|---|---|
| 1 | `# {{ candidate.title }}` | `candidate.title` | H1 제목 |
| 2 | `## When to use` | `candidate.when_to_use[]` | 불릿 |
| 3 | `## When not to use` | `candidate.when_not_to_use[]` | 불릿 |
| 4 | `## Goal` | `candidate.goal` | 한 문단 |
| 5 | `## Workflow` | `candidate.workflow[]` | **숫자 목록** |
| 6 | `## Verification` | `candidate.verification[]` | 불릿 |
| 7 | `## Do not` | `candidate.anti_patterns[]` | 불릿 |
| 8 | `## Output format` | **고정 5항목** (아래) | 불릿 |

### 2.3 Output format — 모든 Skill 공통 5항목 (고정)

```text
- What changed
- Files touched
- Commands run
- Validation result
- Risks or follow-ups
```

> 이 5항목은 archetype과 무관하게 항상 들어갑니다. archetype별 추가 섹션은 §4.B에서 enriched 모드일 때 별도로 첨부됩니다.

---

## 3. Task Archetype (10종)

`spec_compiler.infer_task_archetype` 가 `candidate_text`(name, title, description, goal, example_prompts, workflow, …)에서 키워드 점수로 추론합니다. 매칭 실패 시 `general`.

| Archetype | 트리거 키워드 (일부) | 기본 Workflow 단계 수 | Output 추가 섹션 |
|---|---|---:|---|
| `fix` | fix, failing, broken, 실패, 고쳐, 수정 | 5 | Root cause / What changed / Files touched / Validation / Risks |
| `create` | create, generate, make, 생성, 만들 | 4 | (general fallback) |
| `review` | review, 검토, 리뷰, diff, pr | 4 | Findings / Evidence / Risk level / Suggested fixes / Missing tests |
| `analyze` | analyze, 분석, 요약 | 4 | (general fallback) |
| `refactor` | refactor, 리팩터, 구조 개선 | 5 | (general fallback) |
| `document` | readme, docs, 문서, changelog | 4 | Audience / Updated sections / Examples / Validation / Follow-ups |
| `deploy` | deploy, release, ship, 배포 | 4 | Deployment target / Steps run / Result / Validation / Rollback notes |
| `investigate` | debug, root cause, 원인, 왜 | 4 | Symptoms / Hypotheses / Evidence / Root cause / Next actions |
| `design` | design, ui, ux, figma, 디자인 | 4 | Design goal / Approach / Key decisions / Accessibility / Implementation notes |
| `general` | (fallback) | 5 | Summary / Inputs / Actions / Validation / Risks or follow-ups |

> **주의:** §2.3 의 5항목 `Output format` 은 항상 들어가고, 위 표의 "Output 추가 섹션"은 **enriched 모드의 `### Variable slots` 와 `## Better prompt templates` 등에서 참조용으로** 사용됩니다 (`output_contract.required_sections`).

---

## 4. Enriched 섹션 (기본값: 켜짐)

`enriched=True`이고 `candidate.skill_spec` 이 dict일 때만 추가됩니다 (`promote`는 항상 사전에 `enrich_candidate` 를 호출).

### 4.A 구조

| # | 섹션 제목 | 데이터 출처 |
|---|---|---|
| E1 | `## Prompt quality guide` | `skill_spec.prompt_contract` (intent, input, verification, output) |
| E2 | `### Task contract` | `skill_spec.task_archetype`, `skill_spec.intent_invariant` |
| E3 | `### Variable slots` | `skill_spec.variable_slots[]` |
| E4 | `## Better prompt templates` (Minimal / High-signal / Clarifying) | `skill_spec.better_prompt_templates` |
| E5 | `## Ask when unclear` | `skill_spec.clarifying_questions[]` |
| E6 | `## Quality checklist` | `skill_spec.quality_checklist[]` (고정 7항목, §8.A) |
| E7 | `## Generalization notes` | `skill_spec.generalization_notes[]` (고정 3항목 + archetype 보강) |
| E8 | `## Prompt quality score` | `skill_spec.prompt_quality.score`, `dimensions{}`, `diagnostics[]` |

### 4.B Better prompt templates 3종 (모든 Skill)

| 템플릿 | 용도 | 생성 규칙 |
|---|---|---|
| **Minimal** | 한 줄 짜리 단축 프롬프트 | `goal` + `[작업 대상]` + `verification` + `output` 합성 |
| **High-signal** | 권장 표준 프롬프트 (대상/제약/절차/출력 4블록) | 대상 / 제약 / 절차(번호) / 출력 형식 |
| **Clarifying** | 정보 부족 시 먼저 질문하라는 지시 | `archetype` 명시 + 대상·제약·검증·출력 불명확 시 질문 |

---

## 5. Variable Slots (모든 Skill 공통 베이스)

| 슬롯 | 필수 | 의미 | 기본 placeholder |
|---|:---:|---|---|
| `target` | ✅ | 작업 대상 (파일/diff/로그/URL/문서/이슈/저장소 범위) | `[작업 대상]` |
| `constraints` |  | 수정 범위, 금지사항, 스타일, 호환성, 제외 범위 | `[제약사항]` |
| `verification` | ✅ | 테스트/lint/빌드/수동 확인 등 완료 판정 기준 | `[검증 기준]` |
| `output_format` | ✅ | 응답에 포함할 섹션과 형식 | `[출력 형식]` |
| `branch` |  | 후보 텍스트에서 `branch:` 패턴이 발견될 때만 추가 | `[브랜치]` |
| `date` |  | YYYY-MM-DD 류 날짜 패턴이 발견될 때만 추가 | `[날짜/기간]` |

각 슬롯의 `evidence`는 후보의 example_prompts·anti_patterns·verification에서 자동 추출되어 최대 5건까지 노출됩니다.

---

## 6. Universal Preconditions (2)

생성된 모든 Skill의 `skill_spec.preconditions` 에 자동 포함됩니다.

1. 작업 대상 또는 입력 자료가 명확해야 한다.
2. 완료 여부를 판단할 검증 기준이 있어야 한다.

---

## 7. Universal Risk Controls (3)

`skill_spec.risk_controls` 에 자동 포함됩니다.

1. 특정 파일명, 브랜치, 고객명, 날짜는 가능한 변수로 취급한다.
2. 검증 없이 완료 처리하지 않는다.
3. 예시 프롬프트에만 등장한 세부사항을 Skill 본문에 고정하지 않는다.

---

## 8. 품질 (Quality) 공용 자산

### 8.A Quality checklist — 고정 7항목

`generate_quality_checklist` (모든 archetype 공통):

1. 목표가 한 문장으로 명확한가?
2. 작업 대상 또는 입력 자료가 명시됐는가?
3. 수정 범위와 하지 말아야 할 일이 분리됐는가?
4. 반복 가능한 절차가 순서대로 정의됐는가?
5. 검증 방법과 완료 기준이 포함됐는가?
6. 결과 출력 형식이 정해졌는가?
7. 특정 파일명/브랜치/고객명에 과적합되지 않았는가?

### 8.B Generalization notes — 기본 3항목 + archetype 보강

기본:

1. 예시 프롬프트는 evidence로만 사용하고 Skill 본문에는 일반화된 패턴을 남긴다.
2. 특정 파일명, URL, 브랜치, 날짜는 가능한 variable slot으로 취급한다.
3. 한 번만 등장한 세부 조건은 고정 규칙이 아니라 확인 질문으로 전환한다.

archetype 보강:

- `fix` → "수정형 Skill은 원인 분석과 검증 명령을 항상 포함해야 한다."

### 8.C Prompt Quality Score — 7차원 / 진단 임계값

| 차원 | 의미 | 임계 진단 |
|---|---|---|
| `intent_clarity` | 목표 명료성 | — |
| `input_specificity` | 입력 대상 명시성 | < 70 → "입력 대상이 예시에서 충분히 명확하지 않습니다." |
| `constraint_clarity` | 제약/금지사항 명료성 | < 70 → "수정 범위와 금지사항을 더 명확히 하는 것이 좋습니다." |
| `workflow_reusability` | 절차 재사용성 | — |
| `verification_strength` | 검증 강도 | < 70 → "검증 기준이나 실행 명령이 부족합니다." |
| `output_specificity` | 출력 명세성 | — |
| `generalization_safety` | 일반화 안전성 | < 80 → "특정 파일명/URL/날짜에 과적합될 수 있어 변수화가 필요합니다." |

`score = round(mean(dimensions))` (0~100). 모든 차원 양호 시 진단은 `"Skill 생성을 위한 핵심 계약 정보가 충분합니다."` 한 줄.

### 8.D Clarifying questions — 자동 생성 규칙

각 차원이 < 75 일 때만 해당 질문이 추가됩니다 (중복 제거).

| 트리거 차원 | 추가 질문 |
|---|---|
| `input_specificity` | 작업 대상 파일, diff, 로그, URL, 문서는 무엇인가요? |
| `constraint_clarity` | 반드시 지켜야 할 범위, 금지사항, 스타일 또는 호환성 조건이 있나요? |
| `verification_strength` | 완료 여부는 어떤 테스트, lint, 빌드, 수동 확인으로 검증하면 되나요? |
| `output_specificity` | 결과는 어떤 섹션이나 형식으로 정리하면 되나요? |
| (항상 추가) | 불확실한 정보가 있으면 작업 전에 질문해도 되나요? |

---

## 9. 사전 정의 룰 5종 (`rules.py`)

> Source = `rule` 인 후보의 `when_to_use`/`workflow`/`verification`/`anti_patterns` 는 이 표에서 옵니다. Source = `similarity` 인 후보는 §10 의 일반화된 기본값을 사용합니다.

| name | title | 트리거 키워드 (대표) | Workflow 단계 |
|---|---|---|---:|
| `fix-failing-tests` | Failing Test Fixer | 테스트 실패, pytest, jest, ci 실패, red build | 6 |
| `fix-lint-type-errors` | Lint and Type Error Fixer | lint, 타입 에러, mypy, tsc, ruff, eslint, prettier | 5 |
| `review-current-diff` | Current Diff Reviewer | diff 리뷰, 코드 리뷰, pr 리뷰, 검토 | 4 |
| `update-docs` | Documentation Updater | readme, 문서, docs, 가이드, changelog | 5 |
| `repo-to-infographic` | Repository to Infographic Planner | github, 레포 분석, 인포그래픽, 16:9 | 4 |

각 룰의 `keywords` 는 `classify_prompt` 가 lowercase substring 매칭으로 후보를 분류할 때 사용합니다.

---

## 10. 유사도 기반 후보 (Source = `similarity`) 의 공용 기본값

`rules.py`에 매칭되지 않은 반복/유사 프롬프트 클러스터에 부여되는 공통 텍스트 (`build_similarity_candidates`):

| 필드 | 기본값 |
|---|---|
| `title` | `Similar Prompt Cluster: {top_terms[:3] join ', '}` |
| `goal` | `Turn a repeated semantic prompt pattern into a reusable, verified Codex Skill.` |
| `when_to_use` | 2개: 절차화 필요 / 키워드 규칙으로 잡히지 않는 의미적 반복 |
| `when_not_to_use` | 2개: 예시 프롬프트들이 서로 다른 목표 / 단일 저장소·고객명 의존 |
| `workflow` | 5단계: 검토 → 공통 추출 → 민감정보 제거 → 검증/금지 명세 → 사람 승인 |
| `verification` | 2개: 같은 Skill로 처리 가능성 / 특정 파일·고객·비밀값 비의존 |
| `anti_patterns` | 2개: 유사도 점수만 보고 자동 생성 금지 / 다른 목적 합치기 금지 |

---

## 11. Evidence 섹션 (옵션)

`--evidence` 플래그가 켜진 경우에만 본문 맨 끝에 추가됩니다.

```markdown
## Evidence

- <example_prompt 1 (redacted)>
- <example_prompt 2 (redacted)>
- ...
```

원문 secret은 hook 단계에서 이미 마스킹되어 있어 evidence에도 `[REDACTED_SECRET]` 형태로만 노출됩니다.

---

## 12. 후보 상태 머신 (생성과의 관계)

```text
pending_review ──ignore──▶ ignored
              ──approve─▶ approved
              ──promote─▶ created   (SKILL.md 파일 생성됨)
ignored       ──unignore▶ pending_review
approved      ──promote─▶ created
```

- `created` 상태일 때만 디스크에 `SKILL.md` 파일이 존재해야 한다.
- `ignored` 후보를 `promote`/`create`하려면 `--force` 가 필요하다.
- `promote`는 내부적으로 `enrich_candidate` → `render_skill(enriched=True)` → 파일 쓰기 → 상태 갱신 (`status="created"`, `created_at`) 을 원자적으로 수행한다.

---

## 13. 공용 콘텐츠를 수정할 때 체크리스트

| 변경 대상 | 함께 갱신해야 할 곳 | 테스트 |
|---|---|---|
| 섹션 골격 | `templates/SKILL.md.j2` + 본 문서 §2, §4 | `test_cli.py` (E2E SKILL.md 출력) |
| Output format 5항목 | `templates/SKILL.md.j2` + §2.3 | `test_cli.py` |
| Archetype 추가/삭제 | `spec_compiler._ARCHETYPE_KEYWORDS`, `_DEFAULT_WORKFLOWS`, `_OUTPUT_SECTIONS` + §3 | `test_spec_compiler.py` |
| Variable slot | `extract_variable_slots` + §5 | `test_spec_compiler.py` |
| Quality checklist · 일반화 노트 | `quality.py` 고정 리스트 + §8.A, §8.B | `test_quality.py` |
| 점수 차원 / 임계값 | `quality.compute_quality` + §8.C | `test_quality.py` |
| 사전 정의 룰 | `rules.RULES` + §9 | `test_rules.py` |
| 유사도 기본 텍스트 | `similarity.build_similarity_candidates` + §10 | `test_similarity.py` |

---

> 본 문서는 v0.1.0 현행 코드와 1:1 동기화되어 있습니다. 코드 변경 시 본 표의 "함께 갱신해야 할 곳"에 따라 갱신해 주세요.
