---
name: update-docs
description: Use when the user asks to update README, docs, API documentation, usage guides, or changelog-like documentation.
---

# Documentation Updater

## When to use

- README 업데이트를 요청할 때
- 사용법, API 문서, 개발 가이드 작성이 필요할 때

## When not to use

- 코드 구현이 중심인 요청

## Goal

Update documentation so it accurately reflects the current project behavior.

## Workflow

1. 관련 코드와 기존 문서를 확인한다.
2. 독자와 목적을 판단한다.
3. 설치, 설정, 실행, 예시를 필요한 만큼 추가한다.
4. 낡은 내용을 제거한다.
5. 명령어와 경로를 검증한다.

## Verification

- 문서 명령어가 현재 구조와 맞는지 확인한다.

## Do not

- 확인하지 않은 기능을 문서에 적지 않는다.

## Output format

- What changed
- Files touched
- Commands run
- Validation result
- Risks or follow-ups

## Prompt quality guide

A good prompt for this skill should include:

- Goal: Update documentation so it accurately reflects the current project behavior.
- Target/input: 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위
- Constraints: scope limits, non-goals, style, and compatibility requirements
- Workflow: a repeatable step-by-step process
- Verification: 문서 명령어가 현재 구조와 맞는지 확인한다.
- Output: Audience, Updated sections, Examples, Validation, Follow-ups

### Task contract

- Archetype: `document`
- Intent invariant: Update documentation so it accurately reflects the current project behavior.

### Variable slots

- `target` (required): 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위 → [작업 대상]
- `constraints`: 수정 범위, 금지사항, 스타일, 호환성 조건, 제외 범위 → [제약사항]
- `verification` (required): 테스트, lint, 빌드, 수동 확인 등 완료 여부를 판단할 기준 → [검증 기준]
- `output_format` (required): 결과 응답에 포함해야 할 섹션과 형식 → [출력 형식]

## Better prompt templates

### Minimal

```text
Update documentation so it accurately reflects the current project behavior. 대상은 [작업 대상]입니다. 완료 후 문서 명령어가 현재 구조와 맞는지 확인한다. 기준으로 확인하고 Audience, Updated sections, Examples, Validation, Follow-ups 형식으로 요약해줘.
```

### High-signal

```text
Update documentation so it accurately reflects the current project behavior.

대상:
- [작업 대상]

제약:
- [수정 범위와 금지사항]
- 확인하지 않은 사실은 단정하지 않기

절차:
1. 먼저 목표, 입력, 현재 상태를 확인해줘.
2. 필요한 최소 범위로 작업해줘.
3. 문서 명령어가 현재 구조와 맞는지 확인한다. 기준으로 검증해줘.
4. 실패나 불확실성이 있으면 원인과 후속 조치를 적어줘.

출력:
- Audience, Updated sections, Examples, Validation, Follow-ups
```

### Clarifying

```text
이 요청은 `document` 유형으로 보입니다. 작업 전에 대상, 제약, 검증 기준, 출력 형식이 불명확하면 먼저 질문해줘.
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

- Overall: 75
- intent_clarity: 90
- input_specificity: 55
- constraint_clarity: 60
- workflow_reusability: 90
- verification_strength: 55
- output_specificity: 85
- generalization_safety: 88

### Diagnostics

- 입력 대상이 예시에서 충분히 명확하지 않습니다.
- 수정 범위와 금지사항을 더 명확히 하는 것이 좋습니다.
- 검증 기준이나 실행 명령이 부족합니다.

## Evidence

- README 문서 업데이트하고 사용법 가이드 정리해줘
- docs documentation 사용법을 README에 추가하고 changelog 정리
- 문서 설명 추가하고 설치 실행 예시를 최신 상태로 맞춰줘
