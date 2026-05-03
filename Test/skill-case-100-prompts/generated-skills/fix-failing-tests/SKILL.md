---
name: fix-failing-tests
description: Use when the user asks to fix failing tests, CI failures, pytest/Jest errors, broken test suites, or red builds.
---

# Failing Test Fixer

## When to use

- 테스트 실패 원인 분석을 요청할 때
- CI 실패 또는 red build 수정을 요청할 때

## When not to use

- 새 기능에 대한 테스트를 처음 작성하는 요청

## Goal

Find the root cause of failing tests and apply the smallest safe fix.

## Workflow

1. 실패한 테스트 명령과 에러를 확인한다.
2. 가장 작은 범위로 실패를 재현한다.
3. 관련 파일만 먼저 조사한다.
4. 최소 수정안을 적용한다.
5. 타깃 테스트를 다시 실행한다.
6. 원인, 변경 파일, 실행 명령, 리스크를 요약한다.

## Verification

- 수정 전 실패를 재현했는지 확인한다.
- 수정 후 타깃 테스트가 통과했는지 확인한다.

## Do not

- assertion 삭제 금지
- 무관한 대규모 리팩토링 금지

## Output format

- What changed
- Files touched
- Commands run
- Validation result
- Risks or follow-ups

## Prompt quality guide

A good prompt for this skill should include:

- Goal: Find the root cause of failing tests and apply the smallest safe fix.
- Target/input: 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위
- Constraints: scope limits, non-goals, style, and compatibility requirements
- Workflow: a repeatable step-by-step process
- Verification: 수정 전 실패를 재현했는지 확인한다.; 수정 후 타깃 테스트가 통과했는지 확인한다.
- Output: Root cause, What changed, Files touched, Validation, Risks

### Task contract

- Archetype: `fix`
- Intent invariant: Find the root cause of failing tests and apply the smallest safe fix.

### Variable slots

- `target` (required): 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위 → [작업 대상]
- `constraints`: 수정 범위, 금지사항, 스타일, 호환성 조건, 제외 범위 → [제약사항]
- `verification` (required): 테스트, lint, 빌드, 수동 확인 등 완료 여부를 판단할 기준 → [검증 기준]
- `output_format` (required): 결과 응답에 포함해야 할 섹션과 형식 → [출력 형식]

## Better prompt templates

### Minimal

```text
Find the root cause of failing tests and apply the smallest safe fix. 대상은 [작업 대상]입니다. 완료 후 수정 전 실패를 재현했는지 확인한다.; 수정 후 타깃 테스트가 통과했는지 확인한다. 기준으로 확인하고 Root cause, What changed, Files touched, Validation, Risks 형식으로 요약해줘.
```

### High-signal

```text
Find the root cause of failing tests and apply the smallest safe fix.

대상:
- [작업 대상]

제약:
- [수정 범위와 금지사항]
- 확인하지 않은 사실은 단정하지 않기

절차:
1. 먼저 목표, 입력, 현재 상태를 확인해줘.
2. 필요한 최소 범위로 작업해줘.
3. 수정 전 실패를 재현했는지 확인한다.; 수정 후 타깃 테스트가 통과했는지 확인한다. 기준으로 검증해줘.
4. 실패나 불확실성이 있으면 원인과 후속 조치를 적어줘.

출력:
- Root cause, What changed, Files touched, Validation, Risks
```

### Clarifying

```text
이 요청은 `fix` 유형으로 보입니다. 작업 전에 대상, 제약, 검증 기준, 출력 형식이 불명확하면 먼저 질문해줘.
```

## Ask when unclear

- 작업 대상 파일, diff, 로그, URL, 문서는 무엇인가요?
- 불확실한 정보가 있으면 작업 전에 질문해도 되나요?

## Quality checklist

- 목표가 한 문장으로 명확한가?
- 작업 대상 또는 입력 자료가 명시됐는가?
- 수정 범위와 하지 말아야 할 일이 분리됐는가?
- 반복 가능한 절차가 순서대로 정의됐는가?
- 검증 방법과 완료 기준이 포함됐는가?
- 결과 출력 형식이 정해졌는가?
- 특정 파일명/브랜치/고객명에 과적합되지 않았는가?

## Generalization notes

- 예시 프롬프트는 evidence로만 사용하고 Skill 본문에는 일반화된 패턴을 남긴다.
- 특정 파일명, URL, 브랜치, 날짜는 가능한 variable slot으로 취급한다.
- 한 번만 등장한 세부 조건은 고정 규칙이 아니라 확인 질문으로 전환한다.
- 수정형 Skill은 원인 분석과 검증 명령을 항상 포함해야 한다.

## Prompt quality score

- Overall: 87
- intent_clarity: 90
- input_specificity: 70
- constraint_clarity: 75
- workflow_reusability: 100
- verification_strength: 100
- output_specificity: 85
- generalization_safety: 88

### Diagnostics

- Skill 생성을 위한 핵심 계약 정보가 충분합니다.

## Evidence

- pytest 테스트 실패 고쳐줘. tests/test_api.py 타깃 테스트 재실행 필요
- failing test in pytest needs fix and root cause analysis
- CI 실패 red build야 broken test 원인 분석하고 최소 수정해줘
- jest failing test fix, reproduce the smallest failing case
- 테스트 깨졌어 pytest 로그 보고 원인 찾아 수정해줘
