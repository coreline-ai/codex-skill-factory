# Codex Prompt Skill Factory 제품형 개발 문서

작성 기준일: `2026-05-03`

> **프로젝트 제목:** Codex Prompt Skill Factory  
> **고정 목적:** 누구나 설치해서 Codex 프롬프트 사용 패턴을 로컬에서 수집·분석하고, 반복 요청을 Skill 후보로 제안하며, 사용자가 승인한 후보를 Codex가 바로 사용할 수 있는 Skill로 자동 생성·설치하는 installable CLI 제품.

## 0. 최종 목표

**Codex Prompt Skill Factory는 사용자가 Codex를 쓰는 과정에서 반복되는 프롬프트 패턴을 로컬에서 안전하게 분석하고, 재사용 가능한 Skill 후보를 제안하며, 사용자가 승인한 후보를 Codex가 즉시 사용할 수 있는 Skill로 자동 생성·설치하는 installable CLI 도구다.**

이 프로젝트의 목표는 단순한 repo-local PoC가 아니다. 최종 제품은 누구나 설치해서 다음 흐름을 사용할 수 있어야 한다.

```text
설치
→ init으로 Codex hook/저장소/skill 디렉터리 준비
→ 평소처럼 Codex 사용
→ inbox로 반복 프롬프트 후보 확인
→ promote로 승인된 후보를 Skill로 생성·설치
→ 이후 Codex가 생성된 Skill을 자동 활용
```

## 1. 제품 원칙

| 원칙 | 설명 |
|---|---|
| Local-first | 프롬프트 로그, 분석 결과, Skill 후보는 기본적으로 사용자 로컬에 저장한다. |
| Approval-first | 사용자 승인 없이 Skill을 생성하거나 활성화하지 않는다. |
| Installable | 특정 repo에 복사해 쓰는 스크립트가 아니라 패키지로 설치 가능한 CLI여야 한다. |
| Product UX first | 사용자는 내부 명령 조합을 몰라도 `init`, `inbox`, `promote` 중심으로 사용할 수 있어야 한다. |
| Project-aware | 로그에는 `cwd`, `repo_root`, `project_name`, git metadata를 포함해 프로젝트별 필터링이 가능해야 한다. |
| No secret retention | 저장 전 민감정보를 마스킹하고, 원문 비밀값을 저장하지 않는다. |
| Deterministic by default | 기본 분석은 외부 LLM/API 없이 재현 가능한 로컬 규칙/유사도 분석으로 동작한다. |

## 2. 대상 사용자

- Codex IDE/CLI를 반복적으로 사용하는 개인 개발자
- 여러 프로젝트에서 비슷한 요청을 반복하는 개발자
- 팀 내 공통 Codex Skill 후보를 발견하고 싶은 리드 개발자
- 자신의 프롬프트 사용 패턴을 분석해 작업 자동화 수준을 높이고 싶은 사용자

## 3. 제품 범위

### 3.1 이 제품이 하는 일

- Codex hook 설치/검증
- 사용자 프롬프트와 턴/도구 사용 로그 저장
- 민감정보 마스킹
- 반복/유사 프롬프트 분석
- Skill 후보 생성
- 후보 품질 평가 및 Prompt Contract 생성
- 더 좋은 프롬프트 템플릿, 확인 질문, 품질 체크리스트 생성
- 후보 inbox 제공
- 사용자 승인/무시/생성 상태 관리
- 승인된 후보를 `SKILL.md`로 생성·설치
- dashboard와 analytics 제공
- 제품 동작을 검증하는 doctor 제공

### 3.2 이 제품이 하지 않는 일

- 프롬프트나 로그를 외부 서버로 전송하지 않는다.
- 외부 LLM/API를 필수 의존성으로 삼지 않는다.
- 사용자 승인 없이 Skill을 자동 생성하지 않는다.
- Codex 자체를 수정하지 않는다.
- VS Code Extension, 웹 서버, 원격 동기화는 이번 제품 목표에 포함하지 않는다.
- 팀/조직 단위 SaaS 관리 기능은 포함하지 않는다.

## 4. 제품 UX 명령 체계

사용자는 기본적으로 아래 명령만 알면 된다.

```bash
codex-skill-factory init
codex-skill-factory inbox
codex-skill-factory promote <candidate>
codex-skill-factory dashboard
codex-skill-factory doctor
```

프로젝트 로컬 검증 또는 저장소 전용 Skill이 필요할 때는 `--repo .` 또는 `--project` scope를 사용한다.

```bash
codex-skill-factory init --repo . --yes
codex-skill-factory inbox --repo . --no-interactive
codex-skill-factory promote <candidate> --repo . --yes
codex-skill-factory doctor --repo .
```

고급/내부 명령은 유지하되, 제품 기본 플로우에서는 숨긴다.

```bash
scan
report
preview
approve
ignore
unignore
create
enrich
analytics
```

### 4.1 `init`

목적: 사용자의 Codex 환경을 Skill Factory가 동작 가능한 상태로 만든다.

해야 할 일:

- 저장소 디렉터리 생성
- hook 스크립트 설치 또는 연결
- Codex hook 설정 확인/생성
- Skill 설치 디렉터리 확인/생성
- dashboard/task 설정 생성
- `.gitignore` 또는 로컬 제외 규칙 안내
- `doctor` 자동 실행

기대 출력:

```text
Codex Skill Factory initialized.
Prompt history: <path>
Skill output: <path>
Hooks: OK
Run next: codex-skill-factory inbox
```

### 4.2 `inbox`

목적: 사용자가 처리해야 할 Skill 후보 inbox를 보여준다.

내부 동작:

```text
scan
→ similarity clustering
→ enrichment / quality scoring
→ analytics
→ dashboard data refresh
→ candidate inbox display
```

기대 출력:

```text
3 candidates found

1. fix-failing-tests
   Repeated: 12
   Quality: 87
   Source: rule
   Action: [p]review [m]promote [i]gnore [s]kip

2. similar-release-notes
   Repeated: 5
   Quality: 79
   Source: similarity
```

### 4.3 `promote <candidate>`

목적: 후보 하나를 승인하고 Skill로 생성·설치한다.

내부 동작:

```text
candidate 확인
→ enriched preview 표시
→ 사용자 확인
→ approve
→ create SKILL.md
→ install to skills dir
→ doctor check
```

기대 결과:

```text
Skill installed: <skills-dir>/<candidate>/SKILL.md
Status: created
Doctor: OK
```

### 4.4 `dashboard`

목적: 사용자가 후보, 통계, 품질 점수, 반복 프롬프트를 한눈에 볼 수 있는 정적 HTML dashboard를 생성한다.

기대 산출물:

```text
<factory-data>/dashboard.html
<factory-data>/dashboard.json
```

### 4.5 `doctor`

목적: 설치와 운영 상태를 검증한다.

검사 항목:

- CLI import 가능 여부
- hook 설정 존재 여부
- hook 스크립트 실행 가능 여부
- prompt/turn/tool-use 저장소 쓰기 가능 여부
- candidates/analytics/dashboard 저장소 쓰기 가능 여부
- skills 디렉터리 쓰기 가능 여부
- 최근 로그에서 secret redaction 위반이 없는지 여부

## 5. 아키텍처

### 5.1 구성 요소

```text
codex-skill-factory
├─ CLI UX layer
│  ├─ init
│  ├─ inbox
│  ├─ promote
│  ├─ dashboard
│  └─ doctor
├─ Hook layer
│  ├─ log_user_prompt.py
│  ├─ log_turn_stop.py
│  └─ log_post_tool_use.py
├─ Storage layer
│  ├─ prompt history
│  ├─ candidates
│  ├─ ignored state
│  ├─ analytics
│  └─ dashboard data
├─ Analysis layer
│  ├─ rules
│  ├─ similarity
│  ├─ analytics
│  └─ quality scoring
├─ Skill Spec layer
│  ├─ spec_compiler
│  ├─ enrichment
│  └─ prompt contract
└─ Generation layer
   ├─ SKILL.md template
   ├─ approval state
   └─ skill installation
```

### 5.2 데이터 흐름

```text
Codex UserPromptSubmit
  → hook
  → prompt history jsonl

Codex Stop / PostToolUse
  → hook
  → turns/tool_uses jsonl

codex-skill-factory inbox
  → read logs
  → classify repeated prompts
  → cluster similar prompts
  → compute success/quality signals
  → compile Skill Spec
  → render candidate inbox

codex-skill-factory promote <candidate>
  → preview enriched skill
  → user approval
  → write SKILL.md
  → update candidate status
  → doctor validation
```

### 5.3 저장소 정책

제품은 설치형 도구이므로 저장소 경로는 명시적으로 관리되어야 한다.

필수 저장 파일:

```text
prompt-history/prompts.jsonl
prompt-history/turns.jsonl
prompt-history/tool_uses.jsonl
skill-factory/candidates.json
skill-factory/ignored.json
skill-factory/analytics.json
skill-factory/dashboard.html
skill-factory/dashboard.json
skills/<skill-name>/SKILL.md
```

각 로그 row는 최소한 아래 metadata를 가져야 한다.

```json
{
  "timestamp": "...",
  "event": "UserPromptSubmit",
  "prompt_redacted": "...",
  "normalized_prompt": "...",
  "prompt_hash": "...",
  "cwd": "...",
  "repo_root": "...",
  "project_name": "...",
  "git_branch": "...",
  "git_commit": "...",
  "language": "ko"
}
```

## 6. Skill 후보 모델

후보는 단순 이름/빈도만 가지면 안 된다. 제품형 후보는 생성 가능성과 안전성을 판단할 수 있어야 한다.

```json
{
  "name": "fix-failing-tests",
  "status": "pending_review",
  "source": "rule | similarity",
  "frequency_total": 12,
  "score": 87,
  "example_prompts": [],
  "skill_spec": {
    "task_archetype": "fix",
    "prompt_contract": {
      "intent": "...",
      "input": "...",
      "constraints": [],
      "workflow": [],
      "verification": [],
      "output": {}
    },
    "variable_slots": [],
    "prompt_quality": {
      "score": 87,
      "dimensions": {},
      "diagnostics": []
    },
    "better_prompt_templates": {},
    "clarifying_questions": [],
    "quality_checklist": [],
    "generalization_notes": []
  }
}
```

## 7. 후보 상태 전이

```text
pending_review
  ├─ ignore  → ignored
  ├─ approve → approved
  └─ promote → created

ignored
  └─ unignore → pending_review

approved
  └─ create/promote → created
```

규칙:

- `created` 상태만 실제 Skill 파일이 존재해야 한다.
- `ignored` 후보는 기본 inbox에서 숨긴다.
- `promote`는 `pending_review`와 `approved` 후보 모두 처리할 수 있다.
- `ignored` 후보를 promote하려면 명시적 force가 필요하다.

## 8. 보안 및 개인정보 원칙

- hook은 저장 전에 secret redaction을 수행한다.
- OpenAI API key, GitHub token, bearer token, password/token/secret 패턴은 저장하지 않는다.
- raw payload 전체 저장은 금지한다. 필요 key만 저장한다.
- dashboard에는 redacted prompt만 표시한다.
- 외부 네트워크 호출은 기본 동작에 포함하지 않는다.
- 테스트에는 secret fixture를 포함하되 기대 결과는 `[REDACTED_SECRET]`이어야 한다.

## 9. 현재 구현 자산과 제품화 Gap

### 9.1 이미 구현된 엔진 자산

- prompt/turn/tool-use hook 스크립트
- 설치형 CLI hook command: `hook-user-prompt`, `hook-turn-stop`, `hook-post-tool-use`
- secret redaction
- 규칙 기반 후보 생성
- 유사도 기반 후보 생성
- analytics 계산
- approval 상태 관리
- enrichment / Skill Spec / quality scoring
- SKILL.md 렌더링
- dashboard 렌더링
- 제품 UX command: `init`, `inbox`, `promote`, `doctor`
- 단위/CLI 제품 플로우 테스트

### 9.2 제품형 완성을 위해 필요한 Gap

| Gap | 현재 상태 | 목표 상태 |
|---|---|---|
| 설치 UX | `init` 구현 완료 | 배포 설치 방식 문서화/검증 |
| 기본 UX | `inbox`, `promote` 구현 완료 | 실제 사용자 환경 E2E 확대 |
| 경로 정책 | user scope와 project scope 구현 | user scope fixture/E2E 보강 |
| 자동 설치 | `promote`가 승인·생성·설치 수행 | 실패 시 rollback 테스트 보강 |
| 검증 | 단위/CLI 제품 플로우 테스트 통과 | S1~S10 파일 단위 E2E 테스트로 분리 |
| 문서 | 제품 목표/UX 반영 | 배포/설치 문서 보강 |

## 10. 제품 완료 기준

제품형 v1은 아래 조건을 모두 만족해야 한다.

- `pipx install` 또는 동등한 설치 방식으로 CLI 실행 가능
- `codex-skill-factory init`이 새 환경에서 성공
- Codex hook payload fixture로 prompt/turn/tool-use 로그 생성 가능
- secret이 로그에 저장되지 않음
- `codex-skill-factory inbox`가 후보를 자동 생성·품질 평가·표시
- `codex-skill-factory promote <candidate>`가 Skill을 생성·설치
- 생성된 `SKILL.md`에 Prompt Quality Guide 포함
- `codex-skill-factory dashboard`가 HTML/JSON 생성
- `codex-skill-factory doctor`가 설치/저장소/Skill 상태 검증
- E2E 시나리오 테스트가 모두 통과

## 11. 검증 가능한 시나리오 테스트

아래 시나리오는 제품형 완성 여부를 판단하는 기준이다. 테스트는 임시 HOME과 임시 repo를 사용해 실제 사용자 환경을 오염시키지 않아야 한다.

### S1. 신규 사용자 초기화

| 항목 | 내용 |
|---|---|
| Given | 빈 임시 HOME과 빈 임시 repo |
| When | `codex-skill-factory init --yes` 실행 |
| Then | hook 설정, prompt-history, skill-factory, skills 디렉터리가 생성된다 |
| Verify | `codex-skill-factory doctor`가 OK를 반환한다 |

### S2. 프롬프트 수집과 민감정보 마스킹

| 항목 | 내용 |
|---|---|
| Given | init 완료 상태 |
| When | `UserPromptSubmit` hook fixture에 `api_key=SECRET123`, `ghp_xxx`, `sk-xxx` 포함 |
| Then | `prompts.jsonl`에 `[REDACTED_SECRET]`만 저장된다 |
| Verify | 저장 파일에 원본 secret 문자열이 없어야 한다 |

### S3. 반복 프롬프트 후보 생성

| 항목 | 내용 |
|---|---|
| Given | 테스트 실패 관련 프롬프트 3개 저장 |
| When | `codex-skill-factory inbox --no-interactive` 실행 |
| Then | `fix-failing-tests` 후보가 생성된다 |
| Verify | `candidates.json`에 `status=pending_review`, `skill_spec.prompt_quality.score`가 존재한다 |

### S4. 유사 프롬프트 후보 생성

| 항목 | 내용 |
|---|---|
| Given | 릴리즈 노트/변경 요약처럼 키워드가 조금 다른 유사 프롬프트 3개 저장 |
| When | `codex-skill-factory inbox --no-interactive` 실행 |
| Then | `source=similarity` 후보가 생성된다 |
| Verify | 후보에 평균 유사도, 대표 토큰, Prompt Contract가 존재한다 |

### S5. inbox 사용자 플로우

| 항목 | 내용 |
|---|---|
| Given | 후보 2개 존재 |
| When | `codex-skill-factory inbox --no-interactive` 실행 |
| Then | 후보명, 반복 횟수, quality score, 추천 action이 표시된다 |
| Verify | ignored 후보는 기본 표시에서 제외된다 |

### S6. promote로 Skill 생성·설치

| 항목 | 내용 |
|---|---|
| Given | `fix-failing-tests` 후보가 pending_review 상태 |
| When | `codex-skill-factory promote fix-failing-tests --yes` 실행 |
| Then | 후보가 `created`가 되고 `skills/fix-failing-tests/SKILL.md`가 생성된다 |
| Verify | SKILL.md에 `Prompt quality guide`, `Better prompt templates`, `Quality checklist`가 포함된다 |

### S7. dashboard 생성

| 항목 | 내용 |
|---|---|
| Given | 후보와 analytics 데이터 존재 |
| When | `codex-skill-factory dashboard` 실행 |
| Then | `dashboard.html`, `dashboard.json`이 생성된다 |
| Verify | HTML에 후보명, quality score, better prompt template이 표시된다 |

### S8. doctor 실패 감지

| 항목 | 내용 |
|---|---|
| Given | hook 파일 하나가 삭제된 상태 |
| When | `codex-skill-factory doctor` 실행 |
| Then | 해당 hook check가 실패로 표시된다 |
| Verify | exit code 또는 structured result로 실패를 감지할 수 있다 |

### S9. ignore/unignore 회귀 방지

| 항목 | 내용 |
|---|---|
| Given | 후보 1개 존재 |
| When | `ignore`, `inbox`, `unignore`, `inbox` 순서 실행 |
| Then | ignore 후 숨김, unignore 후 다시 표시된다 |
| Verify | `ignored.json`과 `candidates.json` 상태가 일관된다 |

### S10. 기존 고급 명령 하위 호환

| 항목 | 내용 |
|---|---|
| Given | 기존 scan/report/preview/create를 쓰는 사용자 |
| When | 각 명령 실행 |
| Then | 기존 동작이 깨지지 않는다 |
| Verify | 기존 테스트와 fixture가 그대로 통과한다 |

## 12. 테스트 구현 계획

권장 테스트 파일:

```text
tools/codex-skill-factory/tests/e2e/test_init_flow.py
tools/codex-skill-factory/tests/e2e/test_prompt_capture.py
tools/codex-skill-factory/tests/e2e/test_inbox_flow.py
tools/codex-skill-factory/tests/e2e/test_promote_flow.py
tools/codex-skill-factory/tests/e2e/test_dashboard_doctor.py
```

공통 fixture:

```text
- tmp_home
- tmp_repo
- installed_cli_runner
- hook_payload_factory
- prompt_history_factory
- candidate_assertions
```

필수 테스트 명령:

```bash
pytest -p no:cacheprovider tools/codex-skill-factory
ruff check --no-cache tools/codex-skill-factory/skill_factory tools/codex-skill-factory/tests .codex/hooks
```

제품형 smoke 명령:

```bash
codex-skill-factory init --yes
codex-skill-factory doctor
codex-skill-factory inbox --no-interactive
codex-skill-factory promote fix-failing-tests --yes
codex-skill-factory dashboard
```

## 13. 개발 Phase 계획

### Phase 1. 제품 UX 정리

- `init`, `inbox`, `promote`, `dashboard`, `doctor`를 기본 UX로 고정
- 기존 고급 명령은 내부/advanced 명령으로 유지
- CLI help를 제품 UX 중심으로 재정리

완료 기준:

- 신규 사용자가 README 없이도 `--help`만 보고 golden path를 이해할 수 있다.

### Phase 2. 설치/초기화 구현

- `init` 구현
- 저장소 경로 정책 정리
- hook 설치/검증 구현
- skill 출력 위치 검증 구현

완료 기준:

- S1, S2, S8 시나리오가 통과한다.

### Phase 3. inbox 구현

- `inbox`가 scan, similarity, enrichment, analytics를 한 번에 수행
- non-interactive 출력과 interactive action 모두 지원
- ignored 후보 기본 제외

완료 기준:

- S3, S4, S5, S9 시나리오가 통과한다.

### Phase 4. promote 구현

- 후보 preview, approval, SKILL.md 생성, 설치, 상태 갱신, doctor check를 하나로 묶음
- `--yes`로 CI/e2e 테스트 가능하게 함

완료 기준:

- S6 시나리오가 통과한다.

### Phase 5. dashboard/doctor 제품화

- dashboard에 inbox/action guidance 표시
- doctor가 설치 상태를 구조적으로 검증

완료 기준:

- S7, S8 시나리오가 통과한다.

### Phase 6. 제품형 회귀 테스트 완성

- E2E 시나리오 테스트 추가
- 기존 고급 명령 하위 호환 검증
- packaging/install smoke 검증

완료 기준:

- S1~S10 전체 통과
- 단위 테스트, ruff, smoke 모두 통과

## 14. 출시 전 체크리스트

- [x] `pipx install` 또는 wheel 설치 테스트 완료
- [x] `init`이 빈 project scope 환경에서 성공
- [x] hook fixture로 prompt/turn/tool-use 로그 생성 성공
- [x] secret redaction 테스트 통과
- [x] `inbox`에서 후보 생성/표시 성공
- [x] `promote`로 Skill 생성·설치 성공
- [x] dashboard 생성 성공
- [x] doctor 성공/실패 케이스 검증
- [x] 기존 advanced 명령 하위 호환 확인
- [x] README에 golden path 반영

## 15. 최종 성공 정의

사용자가 아래 네 줄만으로 제품 가치를 경험할 수 있으면 v1 제품 목표를 달성한 것이다.

```text
codex-skill-factory init
(평소처럼 Codex 사용)
codex-skill-factory inbox
codex-skill-factory promote <candidate>
```

그 결과 사용자는 반복 프롬프트를 직접 정리하지 않아도, 자신의 실제 사용 패턴에서 나온 Skill을 승인 기반으로 생성·설치하고 이후 Codex 작업에서 재사용할 수 있어야 한다.
