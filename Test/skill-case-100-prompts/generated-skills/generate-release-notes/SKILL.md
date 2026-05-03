---
name: generate-release-notes
description: Use when the user repeatedly asks to generate release notes from commits, diffs, PRs, or git changes (10 similar examples).
---

# Release Notes Generator

## When to use

- release notes from commits, diffs, PRs, or git changes 요청이 반복되고 입력 대상만 달라질 때
- Release Notes 작업을 같은 절차와 출력 형식으로 자주 처리해야 할 때

## When not to use

- 예시 프롬프트들이 서로 다른 목표나 산출물을 요구하는 경우
- 한 저장소, 고객명, 파일명, 비밀값에만 강하게 의존해 일반화할 수 없는 경우

## Goal

Generate release notes from commits, diffs, PRs, or git changes with a repeatable workflow that keeps target, constraints, verification, and output expectations explicit.

## Workflow

1. 대상 commit range, diff, PR 목록, 변경 요약 중 사용 가능한 입력을 확인한다.
2. 변경사항을 기능, 수정, 문서, 내부 변경, breaking change로 분류한다.
3. 사용자에게 의미 있는 변경만 간결한 release note 문장으로 재작성한다.
4. 버전, 날짜, migration note, known issue가 불명확하면 추정하지 말고 질문 또는 미확인으로 표시한다.
5. 최종 release notes와 검증/리스크를 요청된 형식으로 정리한다.

## Verification

- 작성한 항목이 제공된 diff, commit, PR, changelog 입력에서 근거를 찾을 수 있는지 확인한다.
- 확인되지 않은 버전, 날짜, 사용자 영향도를 임의로 추가하지 않았는지 확인한다.

## Do not

- 커밋 메시지만 보고 사용자 영향도나 breaking change를 과장하지 않는다.
- 확인되지 않은 릴리즈 날짜, 버전, 고객명을 고정값으로 쓰지 않는다.

## Output format

- Release summary
- Notable changes
- Breaking changes or migrations
- Validation
- Risks or follow-ups

## Prompt quality guide

A good prompt for this skill should include:

- Goal: Generate release notes from commits, diffs, PRs, or git changes with a repeatable workflow that keeps target, constraints, verification, and output expectations explicit.
- Target/input: 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위
- Constraints: scope limits, non-goals, style, and compatibility requirements
- Workflow: a repeatable step-by-step process
- Verification: 작성한 항목이 제공된 diff, commit, PR, changelog 입력에서 근거를 찾을 수 있는지 확인한다.; 확인되지 않은 버전, 날짜, 사용자 영향도를 임의로 추가하지 않았는지 확인한다.
- Output: Release summary, Notable changes, Breaking changes or migrations, Validation, Risks or follow-ups

### Task contract

- Archetype: `document`
- Intent invariant: Generate release notes from commits, diffs, PRs, or git changes with a repeatable workflow that keeps target, constraints, verification, and output expectations explicit.

### Variable slots

- `target` (required): 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위 → [작업 대상]
- `constraints`: 수정 범위, 금지사항, 스타일, 호환성 조건, 제외 범위 → [제약사항]
- `verification` (required): 테스트, lint, 빌드, 수동 확인 등 완료 여부를 판단할 기준 → [검증 기준]
- `output_format` (required): 결과 응답에 포함해야 할 섹션과 형식 → [출력 형식]

## Better prompt templates

### Minimal

```text
Generate release notes from commits, diffs, PRs, or git changes with a repeatable workflow that keeps target, constraints, verification, and output expectations explicit. 대상은 [작업 대상]입니다. 완료 후 작성한 항목이 제공된 diff, commit, PR, changelog 입력에서 근거를 찾을 수 있는지 확인한다.; 확인되지 않은 버전, 날짜, 사용자 영향도를 임의로 추가하지 않았는지 확인한다. 기준으로 확인하고 Release summary, Notable changes, Breaking changes or migrations, Validation, Risks or follow-ups 형식으로 요약해줘.
```

### High-signal

```text
Generate release notes from commits, diffs, PRs, or git changes with a repeatable workflow that keeps target, constraints, verification, and output expectations explicit.

대상:
- [작업 대상]

제약:
- [수정 범위와 금지사항]
- 확인하지 않은 사실은 단정하지 않기

절차:
1. 먼저 목표, 입력, 현재 상태를 확인해줘.
2. 필요한 최소 범위로 작업해줘.
3. 작성한 항목이 제공된 diff, commit, PR, changelog 입력에서 근거를 찾을 수 있는지 확인한다.; 확인되지 않은 버전, 날짜, 사용자 영향도를 임의로 추가하지 않았는지 확인한다. 기준으로 검증해줘.
4. 실패나 불확실성이 있으면 원인과 후속 조치를 적어줘.

출력:
- Release summary, Notable changes, Breaking changes or migrations, Validation, Risks or follow-ups
```

### Clarifying

```text
이 요청은 `document` 유형으로 보입니다. 작업 전에 대상, 제약, 검증 기준, 출력 형식이 불명확하면 먼저 질문해줘.
```

## Ask when unclear

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

- Overall: 85
- intent_clarity: 90
- input_specificity: 100
- constraint_clarity: 75
- workflow_reusability: 90
- verification_strength: 70
- output_specificity: 85
- generalization_safety: 88

## Install readiness

- Grade: install_recommended
- Recommendation: 승인 후 바로 promote해도 좋습니다.

### Diagnostics

- Skill 생성을 위한 핵심 계약 정보가 충분합니다.

## Evidence

- make version release notes based on commit history and user visible changes
- draft release communication using commit messages and upgrade notes
- write a release announcement from merged commits and categorize changes
- generate release summary from git commits with breaking changes and migration notes
- prepare release notes from current commits and summarize notable changes
