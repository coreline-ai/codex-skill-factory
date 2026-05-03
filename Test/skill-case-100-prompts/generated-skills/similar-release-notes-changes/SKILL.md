---
name: similar-release-notes-changes
description: Use when the user repeatedly asks semantically similar requests represented by this prompt cluster (10 examples).
---

# Similar Prompt Cluster: release, notes, changes

## When to use

- 유사한 프롬프트가 반복되어 절차화된 Skill 후보가 필요할 때
- 키워드 규칙으로는 잡히지 않지만 의미상 같은 작업이 반복될 때

## When not to use

- 예시 프롬프트들이 서로 다른 목표를 갖는 경우
- 한 저장소나 특정 고객명에만 강하게 의존하는 경우

## Goal

Turn a repeated semantic prompt pattern into a reusable, verified Codex Skill.

## Workflow

1. 대표 예시 프롬프트들을 검토한다.
2. 공통 목표와 반복 절차를 추출한다.
3. 프로젝트 고유 정보나 민감정보를 제거한다.
4. 검증 방법과 금지 사항을 명확히 작성한다.
5. 생성 전 사람이 후보를 승인한다.

## Verification

- 예시 프롬프트들이 같은 Skill로 처리 가능한지 확인한다.
- 생성된 Skill이 특정 파일/고객/비밀값에 의존하지 않는지 확인한다.

## Do not

- 유사도 점수만 보고 자동 생성하지 않는다.
- 서로 다른 목적의 프롬프트를 하나의 Skill로 합치지 않는다.

## Output format

- What changed
- Files touched
- Commands run
- Validation result
- Risks or follow-ups

## Prompt quality guide

A good prompt for this skill should include:

- Goal: Turn a repeated semantic prompt pattern into a reusable, verified Codex Skill.
- Target/input: 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위
- Constraints: scope limits, non-goals, style, and compatibility requirements
- Workflow: a repeatable step-by-step process
- Verification: 예시 프롬프트들이 같은 Skill로 처리 가능한지 확인한다.; 생성된 Skill이 특정 파일/고객/비밀값에 의존하지 않는지 확인한다.
- Output: Summary, Inputs, Actions, Validation, Risks or follow-ups

### Task contract

- Archetype: `create`
- Intent invariant: Turn a repeated semantic prompt pattern into a reusable, verified Codex Skill.

### Variable slots

- `target` (required): 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위 → [작업 대상]
- `constraints`: 수정 범위, 금지사항, 스타일, 호환성 조건, 제외 범위 → [제약사항]
- `verification` (required): 테스트, lint, 빌드, 수동 확인 등 완료 여부를 판단할 기준 → [검증 기준]
- `output_format` (required): 결과 응답에 포함해야 할 섹션과 형식 → [출력 형식]

## Better prompt templates

### Minimal

```text
Turn a repeated semantic prompt pattern into a reusable, verified Codex Skill. 대상은 [작업 대상]입니다. 완료 후 예시 프롬프트들이 같은 Skill로 처리 가능한지 확인한다.; 생성된 Skill이 특정 파일/고객/비밀값에 의존하지 않는지 확인한다. 기준으로 확인하고 Summary, Inputs, Actions, Validation, Risks or follow-ups 형식으로 요약해줘.
```

### High-signal

```text
Turn a repeated semantic prompt pattern into a reusable, verified Codex Skill.

대상:
- [작업 대상]

제약:
- [수정 범위와 금지사항]
- 확인하지 않은 사실은 단정하지 않기

절차:
1. 먼저 목표, 입력, 현재 상태를 확인해줘.
2. 필요한 최소 범위로 작업해줘.
3. 예시 프롬프트들이 같은 Skill로 처리 가능한지 확인한다.; 생성된 Skill이 특정 파일/고객/비밀값에 의존하지 않는지 확인한다. 기준으로 검증해줘.
4. 실패나 불확실성이 있으면 원인과 후속 조치를 적어줘.

출력:
- Summary, Inputs, Actions, Validation, Risks or follow-ups
```

### Clarifying

```text
이 요청은 `create` 유형으로 보입니다. 작업 전에 대상, 제약, 검증 기준, 출력 형식이 불명확하면 먼저 질문해줘.
```

## Ask when unclear

- 작업 대상 파일, diff, 로그, URL, 문서는 무엇인가요?
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

- Overall: 79
- intent_clarity: 90
- input_specificity: 55
- constraint_clarity: 75
- workflow_reusability: 90
- verification_strength: 70
- output_specificity: 85
- generalization_safety: 88

### Diagnostics

- 입력 대상이 예시에서 충분히 명확하지 않습니다.

## Evidence

- prepare release notes from current commits and summarize notable changes
- generate release summary from git commits with breaking changes and migration notes
- write a release announcement from merged commits and categorize changes
- make version release notes based on commit history and user visible changes
- draft release communication using commit messages and upgrade notes
