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
| 8 | `## Output format` | `skill_spec.output_contract.required_sections` 또는 fallback 5항목 | 불릿 |

### 2.3 Output format — archetype 기반 출력 계약

`enriched=True`이고 `candidate.skill_spec` 이 존재하면 `spec_compiler.py`가 만든 `output_contract.required_sections`를 직접 렌더링한다. 기본은 `task_archetype`별 출력 섹션이며, 유사도 domain profile이 `candidate.output_sections`를 제공하면 해당 domain별 출력 섹션이 우선한다.

`enriched=False` 또는 legacy 후보처럼 `skill_spec`이 없는 경우에만 아래 fallback 5항목을 사용한다.

```text
- What changed
- Files touched
- Commands run
- Validation result
- Risks or follow-ups
```

---

## 3. Task Archetype (10종)

`spec_compiler.infer_task_archetype` 가 `candidate_text`(name, title, description, goal, example_prompts, workflow, …)에서 키워드 점수로 추론합니다. 매칭 실패 시 `general`.

| Archetype | 트리거 키워드 (일부) | 기본 Workflow 단계 수 | Output 추가 섹션 |
|---|---|---:|---|
| `fix` | fix, failing, broken, 실패, 고쳐, 수정 | 5 | Root cause / What changed / Files touched / Validation / Risks |
| `create` | create, generate, make, 생성, 만들 | 4 | Deliverable / Inputs used / Key decisions / Validation / Follow-ups |
| `review` | review, 검토, 리뷰, diff, pr | 4 | Findings / Evidence / Risk level / Suggested fixes / Missing tests |
| `analyze` | analyze, 분석, 요약 | 4 | Question / Evidence / Findings / Confidence / Next actions |
| `refactor` | refactor, 리팩터, 구조 개선 | 5 | Goal / Files changed / Behavior preserved / Validation / Risks |
| `document` | readme, docs, 문서, changelog | 4 | Audience / Updated sections / Examples / Validation / Follow-ups |
| `deploy` | deploy, release, ship, 배포 | 4 | Deployment target / Steps run / Result / Validation / Rollback notes |
| `investigate` | debug, root cause, 원인, 왜 | 4 | Symptoms / Hypotheses / Evidence / Root cause / Next actions |
| `design` | design, ui, ux, figma, 디자인 | 4 | Design goal / Approach / Key decisions / Accessibility / Implementation notes |
| `general` | (fallback) | 5 | Summary / Inputs / Actions / Validation / Risks or follow-ups |

> **주의:** 현재 구현에서 enriched 렌더링은 위 표의 `output_contract.required_sections`를 `## Output format`에 직접 사용합니다. fallback 5항목은 legacy/비-enriched 렌더링용입니다.

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
| E9 | `## Install readiness` | `skill_spec.prompt_quality.install_readiness` (grade, recommendation, blockers) |

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
| `target` | ✅ | 작업 대상 (파일/diff/commit/PR/log/URL/문서/이슈/저장소 범위) | `[작업 대상]` |
| `constraints` |  | 수정 범위, 금지사항, 스타일, 호환성, 제외 범위 | `[제약사항]` |
| `verification` | ✅ | 테스트/lint/빌드/수동 확인 등 완료 판정 기준 | `[검증 기준]` |
| `output_format` | ✅ | 응답에 포함할 섹션과 형식 | `[출력 형식]` |
| `branch` |  | 후보 텍스트에서 `branch:` 패턴이 발견될 때만 추가 | `[브랜치]` |
| `date` |  | YYYY-MM-DD 류 날짜 패턴이 발견될 때만 추가 | `[날짜/기간]` |

각 슬롯의 `evidence`는 후보의 example_prompts·anti_patterns·verification에서 자동 추출되어 최대 5건까지 노출됩니다. `target`은 파일/URL뿐 아니라 `latest diff`, `git changes`, `commits`, `PR list`, `logs`, `screenshot`, `metrics`, `README` 같은 일반 입력 단서도 추출합니다.

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

`score = round(mean(dimensions))` (0~100). `generalization_safety`는 `diff`, `commits`, `logs` 같은 일반 입력 단서가 아니라 실제 파일 경로, URL, 날짜 같은 구체값이 과도할 때만 감점합니다. 모든 차원 양호 시 진단은 `"Skill 생성을 위한 핵심 계약 정보가 충분합니다."` 한 줄.

### 8.D Clarifying questions — 자동 생성 규칙

각 차원이 < 75 일 때만 해당 질문이 추가됩니다 (중복 제거).

| 트리거 차원 | 추가 질문 |
|---|---|
| `input_specificity` | 작업 대상 파일, diff, 로그, URL, 문서는 무엇인가요? |
| `constraint_clarity` | 반드시 지켜야 할 범위, 금지사항, 스타일 또는 호환성 조건이 있나요? |
| `verification_strength` | 완료 여부는 어떤 테스트, lint, 빌드, 수동 확인으로 검증하면 되나요? |
| `output_specificity` | 결과는 어떤 섹션이나 형식으로 정리하면 되나요? |
| (항상 추가) | 불확실한 정보가 있으면 작업 전에 질문해도 되나요? |

### 8.E Install readiness — 설치 추천 등급

`compute_quality`는 `prompt_quality.install_readiness`를 함께 생성한다.

| Grade | 조건 | Recommendation |
|---|---|---|
| `install_recommended` | score ≥ 85 이고 blocking issue 없음 | 승인 후 바로 `promote` 가능 |
| `review_recommended` | score ≥ 72 이고 blocking issue 1개 이하 | `preview`에서 변수/검증 기준 확인 후 `promote` |
| `needs_improvement` | 그 외 | 후보 보강 또는 추가 반복 예시 수집 |

Blocking issue는 입력 대상 부족, 검증 기준 부족, 과적합 위험이 기준 이하일 때 생성된다.

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

## 10. 유사도 기반 후보 (Source = `similarity`) 의 후보 합성

`rules.py`에 매칭되지 않은 반복/유사 프롬프트 클러스터는 `build_similarity_candidates`가 로컬·결정론적으로 action/domain profile을 추론해 구체적 후보로 합성한다. 목적은 “유사 프롬프트 클러스터를 Skill로 만들라”는 메타 Skill이 아니라, 사용자가 실제로 반복 요청한 작업 Skill을 제안하는 것이다.

| 필드 | 기본값 |
|---|---|
| `name` | `{action}-{domain}` 예: `generate-release-notes`; fallback은 `handle-{top_terms}` |
| `title` | domain/action별 구체 제목 예: `Release Notes Generator` |
| `goal` | `{action} {domain.object_phrase}` 중심의 반복 작업 목표 |
| `when_to_use` | 입력 대상만 달라지는 같은 domain/action 작업 반복 |
| `when_not_to_use` | 서로 다른 목표 / 단일 저장소·고객·파일·비밀값 의존 |
| `workflow` | domain profile별 절차. fallback은 공통 목표 확인 → 변수/제약 분리 → 검증 → 구조화 출력 |
| `verification` | domain profile별 근거/검증 기준. fallback은 같은 목표/절차 가능성과 과적합 여부 |
| `anti_patterns` | domain profile별 금지 사항 + 추측/과적합 방지 |
| `output_sections` | domain profile이 있을 때 `output_contract.required_sections`에 우선 적용 |
| `similarity.intent_profile` | 추론된 `action`, `domain`, `domain_label` 저장 |

현재 기본 domain profile은 `release-notes`, `documentation`, `diff-review`, `infographic`, `data-analysis`이며, profile에 없는 클러스터는 top terms 기반의 안전한 fallback을 사용한다.

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
