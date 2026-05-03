---
name: review-current-diff
description: Use when the user asks to review the current git diff, PR changes, code changes, or wants risk and bug analysis before committing.
---

# Current Diff Reviewer

## When to use

- 현재 git diff 리뷰를 요청할 때
- PR 전 리스크 점검을 요청할 때

## When not to use

- 코드 구현 자체를 요청하는 경우

## Goal

Review the current changes for correctness, risk, maintainability, and missing tests.

## Workflow

1. 현재 git diff를 확인한다.
2. 변경 의도를 추론한다.
3. 버그 가능성, 회귀 위험, 누락 테스트를 찾는다.
4. 중요도 높은 피드백부터 제시한다.

## Verification

- diff 근거로만 리뷰한다.

## Do not

- 사소한 스타일만 과도하게 지적하지 않는다.

## Output format

- What changed
- Files touched
- Commands run
- Validation result
- Risks or follow-ups

## Prompt quality guide

A good prompt for this skill should include:

- Goal: Review the current changes for correctness, risk, maintainability, and missing tests.
- Target/input: 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위
- Constraints: scope limits, non-goals, style, and compatibility requirements
- Workflow: a repeatable step-by-step process
- Verification: diff 근거로만 리뷰한다.
- Output: Findings, Evidence, Risk level, Suggested fixes, Missing tests

### Task contract

- Archetype: `review`
- Intent invariant: Review the current changes for correctness, risk, maintainability, and missing tests.

### Variable slots

- `target` (required): 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위 → [작업 대상]
- `constraints`: 수정 범위, 금지사항, 스타일, 호환성 조건, 제외 범위 → [제약사항]
- `verification` (required): 테스트, lint, 빌드, 수동 확인 등 완료 여부를 판단할 기준 → [검증 기준]
- `output_format` (required): 결과 응답에 포함해야 할 섹션과 형식 → [출력 형식]

## Better prompt templates

### Minimal

```text
Review the current changes for correctness, risk, maintainability, and missing tests. 대상은 [작업 대상]입니다. 완료 후 diff 근거로만 리뷰한다. 기준으로 확인하고 Findings, Evidence, Risk level, Suggested fixes, Missing tests 형식으로 요약해줘.
```

### High-signal

```text
Review the current changes for correctness, risk, maintainability, and missing tests.

대상:
- [작업 대상]

제약:
- [수정 범위와 금지사항]
- 확인하지 않은 사실은 단정하지 않기

절차:
1. 먼저 목표, 입력, 현재 상태를 확인해줘.
2. 필요한 최소 범위로 작업해줘.
3. diff 근거로만 리뷰한다. 기준으로 검증해줘.
4. 실패나 불확실성이 있으면 원인과 후속 조치를 적어줘.

출력:
- Findings, Evidence, Risk level, Suggested fixes, Missing tests
```

### Clarifying

```text
이 요청은 `review` 유형으로 보입니다. 작업 전에 대상, 제약, 검증 기준, 출력 형식이 불명확하면 먼저 질문해줘.
```

## Ask when unclear

- 작업 대상 파일, diff, 로그, URL, 문서는 무엇인가요?
- 반드시 지켜야 할 범위, 금지사항, 스타일 또는 호환성 조건이 있나요?
- 완료 여부는 어떤 테스트, lint, 빌드, 수동 확인으로 검증하면 되나요?
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

## Prompt quality score

- Overall: 73
- intent_clarity: 90
- input_specificity: 55
- constraint_clarity: 60
- workflow_reusability: 80
- verification_strength: 55
- output_specificity: 85
- generalization_safety: 88

### Diagnostics

- 입력 대상이 예시에서 충분히 명확하지 않습니다.
- 수정 범위와 금지사항을 더 명확히 하는 것이 좋습니다.
- 검증 기준이나 실행 명령이 부족합니다.

## Evidence

- 현재 diff 리뷰하고 PR 전 위험 검토해줘
- review this current git diff before merge
- 변경사항 검토하고 누락 테스트와 회귀 위험 찾아줘
- PR 리뷰 관점으로 코드 리뷰 진행해줘
