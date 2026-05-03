# Codex Prompt Skill Factory 제품형 개발계획 전문가 리뷰

작성일: `2026-05-03`

> **프로젝트 제목:** Codex Prompt Skill Factory  
> **고정 목적:** 누구나 설치해서 Codex 프롬프트 사용 패턴을 로컬에서 수집·분석하고, 반복 요청을 Skill 후보로 제안하며, 사용자가 승인한 후보를 Codex가 바로 사용할 수 있는 Skill로 자동 생성·설치하는 installable CLI 제품.

## Verdict

**READY_WITH_CONCERNS** — 제품 목표와 Golden Path는 이제 명확하다. 다만 바로 구현에 들어가기 전, `init`의 설치 범위와 저장소 경로 정책을 더 강하게 잠가야 한다. 이 두 가지가 흔들리면 E2E 테스트, 사용자 경험, 보안 모델이 모두 흔들린다.

## 리뷰 기준

대상 문서:

- `docs/codex_prompt_skill_factory_dev_doc.md`
- `dev-plan/implement_20260503_114217.md`

검토 관점:

- installable CLI 제품성
- 사용자 Golden Path
- Codex hook 현실성
- 로컬 보안/개인정보
- 테스트 가능성
- 확장 없이 v1 완성 가능성

참고한 공식 문서:

- OpenAI Codex Hooks 문서: https://developers.openai.com/codex/hooks

## 핵심 판단

현재 문서는 이전의 repo-local PoC 방향에서 벗어나 **제품형 CLI 목표**를 제대로 잡았다. 특히 아래 결정은 좋다.

- 기본 UX를 `init → inbox → promote`로 단순화
- 고급 명령을 내부 building block으로 남김
- Local-first / Approval-first / Deterministic by default 원칙 명시
- S1~S10 시나리오 테스트를 제품 완료 기준으로 격상
- Skill 후보 모델에 `skill_spec`, quality, prompt contract 포함

하지만 제품형으로 제작하려면 다음 3개 결정을 구현 전에 확정해야 한다.

```text
1. init은 user-level hooks를 기본으로 설치할 것인가, project-level hooks를 기본으로 설치할 것인가?
2. prompt-history / candidates / skills의 기본 저장소는 어디인가?
3. doctor는 단순 표시인가, CI가 실패를 감지할 수 있는 계약인가?
```

## 공식 Codex Hook 문서 기반 확인 사항

OpenAI Codex Hooks 문서 기준으로 현재 계획과 맞는 점:

- hooks는 `config.toml` feature flag가 필요하다.
- Codex는 `~/.codex/hooks.json`, `~/.codex/config.toml`, `<repo>/.codex/hooks.json`, `<repo>/.codex/config.toml` 위치를 지원한다.
- `UserPromptSubmit`, `Stop`, `PostToolUse`는 모두 turn scope에서 동작한다.
- project-local hooks는 신뢰된 프로젝트에서만 로드된다.
- 여러 hook source가 있으면 matching hook이 모두 실행된다.

전문가 리뷰 결론:

- `init`은 **user-level 설치를 기본값**으로 두는 것이 제품 목표와 가장 잘 맞다.
- project-level 설치는 `--project` 옵션으로 제공하는 것이 맞다.
- hook command는 상대 경로보다 absolute path 또는 안정적 root resolution을 써야 한다.

## 아키텍처 리뷰

### 현재 문서 아키텍처

```text
CLI UX layer
  ├─ init
  ├─ inbox
  ├─ promote
  ├─ dashboard
  └─ doctor

Engine layer
  ├─ hooks
  ├─ storage
  ├─ analysis
  ├─ skill spec
  └─ generation
```

평가: **좋음.** 제품 UX layer와 engine layer를 나눈 것이 맞다.

### 반드시 잠가야 할 저장소 정책

문서에는 필수 저장 파일이 정의되어 있지만, 실제 경로 결정이 아직 부족하다. 아래처럼 계약화하는 것이 좋다.

```text
기본 user scope:
~/.codex/prompt-history/
~/.codex/skill-factory/
~/.codex/skills/

project scope 옵션:
<repo>/.codex-prompt-history/
<repo>/.codex-skill-suggestions/
<repo>/.codex/skills/
```

권장 정책:

| 항목 | 권장 기본값 | 이유 |
|---|---|---|
| hook 설치 | user scope | 누구나 설치 후 모든 Codex 작업에서 동작 |
| prompt history | user scope | 사용자의 반복 패턴을 전체적으로 분석 가능 |
| candidates | user scope + project metadata filter | 공용 후보와 프로젝트 후보를 구분 가능 |
| generated skills | user scope | 생성 후 즉시 재사용 가능 |
| project-local mode | explicit `--project` | repo 전용 Skill이 필요한 경우만 사용 |

## Top risks

### P0. `init` 설치 범위가 모호함

현재 문서는 installable product를 목표로 하지만 repo-local 구현 자산이 남아 있다. `init`의 기본 scope를 명확히 하지 않으면 사용자마다 로그/Skill 위치가 달라진다.

권장:

```bash
codex-skill-factory init              # user scope 기본
codex-skill-factory init --project    # 현재 repo 전용
codex-skill-factory init --dry-run    # 변경 내용 미리보기
```

### P0. doctor 실패 계약이 부족함

문서는 doctor가 검증한다고 되어 있지만, 제품형 테스트에는 exit code/structured result가 필요하다.

권장:

```bash
codex-skill-factory doctor --json
```

예상 출력:

```json
{
  "ok": false,
  "checks": [
    {"name": "hooks.user_prompt_submit", "ok": false, "path": "..."}
  ]
}
```

### P1. Hook command path 안정성

공식 문서상 commands run with session cwd이고, repo-local hooks는 subdirectory에서 시작될 수 있다. 따라서 `.codex/hooks/...` 같은 상대 경로는 제품형 설치에 취약하다.

권장:

- user scope: absolute path 사용
- project scope: git root 기반 path 사용
- doctor에서 실제 command path 존재 여부 검증

### P1. 시나리오 테스트는 좋지만 fixture contract가 더 필요함

S1~S10은 좋다. 하지만 각 테스트가 어떤 fixture를 쓰는지 더 구체화하면 구현 속도가 빨라진다.

권장 fixture:

```text
tmp_home
codex_home
tmp_repo
factory_paths
hook_payloads
cli_runner
assert_jsonl_redacted
assert_candidate_created
```

### P2. `inbox` interactive UX와 CI UX가 섞일 위험

문서에는 `inbox --no-interactive`가 있다. 좋다. 실제 구현에서는 interactive prompt가 테스트를 block하지 않도록 기본값/옵션을 명확히 해야 한다.

권장:

- TTY면 interactive 기본
- non-TTY면 no-interactive 기본
- CI에서는 항상 `--no-interactive`

## Required changes before implementation

1. `init` scope 계약 확정
   - default: user scope
   - option: `--project`
   - option: `--dry-run`
   - option: `--yes`

2. Storage path API 확정
   - `Paths(scope="user" | "project")`
   - `project metadata`는 로그 row에 저장
   - 테스트는 temp HOME으로 user scope를 격리

3. `doctor` automation contract 확정
   - human table output
   - `--json` output
   - non-zero exit on failed required checks

4. E2E fixture 우선 구현
   - 코드보다 fixture가 먼저다.
   - S1~S10이 같은 fixture 계층을 공유해야 한다.

5. `promote` safety contract 확정
   - preview shown unless `--yes`
   - ignored candidate requires `--force`
   - existing Skill requires `--overwrite`
   - created status only after file write succeeds

## Scenario coverage review

| Scenario | 상태 | 리뷰 |
|---|---:|---|
| S1 init | 좋음 | `--dry-run`, user/project scope 검증 추가 권장 |
| S2 redaction | 좋음 | raw payload 전체 저장 금지 assertion 필요 |
| S3 repeated candidate | 좋음 | frequency threshold와 min examples 명시 권장 |
| S4 similarity candidate | 좋음 | threshold 고정 fixture 필요 |
| S5 inbox | 좋음 | TTY/non-TTY 동작 분리 필요 |
| S6 promote | 핵심 | created 상태 갱신 순서와 rollback 테스트 필요 |
| S7 dashboard | 좋음 | HTML뿐 아니라 JSON schema 검증 권장 |
| S8 doctor failure | 핵심 | exit code/JSON result 필수 |
| S9 ignore/unignore | 좋음 | scan 이후 ignored 상태 유지 검증 필요 |
| S10 compatibility | 필수 | 기존 CLI 테스트를 삭제하지 말고 유지해야 함 |

## Recommended implementation sequence

```text
1. Paths/scope abstraction
2. doctor --json + exit code contract
3. init --yes --dry-run user scope
4. E2E fixtures for temp HOME/temp repo
5. inbox --no-interactive
6. promote --yes
7. dashboard schema assertions
8. packaging/install smoke
```

이 순서가 좋은 이유:

- 경로와 doctor가 먼저 안정되어야 나머지 E2E가 흔들리지 않는다.
- inbox/promote는 기존 scan/enrich/create engine을 조합하면 되므로 뒤로 미뤄도 된다.
- packaging smoke는 마지막에 해야 실제 설치형 UX를 검증할 수 있다.

## Test diagram

```text
tmp_home
  └─ .codex/
      ├─ config.toml / hooks.json
      ├─ hooks/*.py
      ├─ prompt-history/*.jsonl
      ├─ skill-factory/*.json|html
      └─ skills/<skill>/SKILL.md

tmp_repo
  └─ used only as cwd/repo metadata source

E2E flow
  init --yes
    ↓
  hook fixtures write logs
    ↓
  inbox --no-interactive
    ↓
  candidates.json + analytics.json
    ↓
  promote <candidate> --yes
    ↓
  skills/<candidate>/SKILL.md
    ↓
  doctor --json
```

## Final recommendation

문서는 구현에 들어갈 수 있을 만큼 충분히 좋아졌다. 단, 바로 `inbox`나 `promote`부터 만들지 말고 **Paths/scope와 doctor contract를 먼저 구현**해야 한다.

최종 판정:

```text
READY_WITH_CONCERNS
```

Must-fix before coding:

1. user/project scope 경로 계약
2. doctor JSON/exit code 계약
3. E2E temp HOME fixture 계약

이 3개만 잠그면 현재 계획은 제품형 구현으로 진행해도 된다.
