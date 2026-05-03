---
name: repo-to-infographic
description: Use when the user asks to analyze a GitHub repository and create a concise 16:9 infographic brief or image-generation prompt.
---

# Repository to Infographic Planner

## When to use

- GitHub 저장소를 분석해 인포그래픽을 만들 때
- 16:9 요약 이미지 프롬프트가 필요할 때

## When not to use

- 코드 수정이나 테스트 실행이 중심인 개발 작업

## Goal

Turn repository information into a clear, attractive, accurate infographic plan.

## Workflow

1. README와 주요 구조를 확인한다.
2. 목적, 기능, 파이프라인, 기술 스택, 출력 결과를 추출한다.
3. 5개 이하의 섹션으로 정리한다.
4. 16:9 이미지에 맞는 레이아웃과 스타일 지시를 작성한다.

## Verification

- README에서 확인한 사실만 핵심 수치로 사용한다.
- 텍스트가 이미지에서 읽기 쉬운 길이인지 확인한다.

## Do not

- 확인하지 않은 수치를 추가하지 않는다.
- 참조 이미지의 주제까지 복사하지 않는다.

## Output format

- Deliverable
- Inputs used
- Key decisions
- Validation
- Follow-ups

## Prompt quality guide

A good prompt for this skill should include:

- Goal: Turn repository information into a clear, attractive, accurate infographic plan.
- Target/input: 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위
- Constraints: scope limits, non-goals, style, and compatibility requirements
- Workflow: a repeatable step-by-step process
- Verification: README에서 확인한 사실만 핵심 수치로 사용한다.; 텍스트가 이미지에서 읽기 쉬운 길이인지 확인한다.
- Output: Deliverable, Inputs used, Key decisions, Validation, Follow-ups

### Task contract

- Archetype: `create`
- Intent invariant: Turn repository information into a clear, attractive, accurate infographic plan.

### Variable slots

- `target` (required): 작업 대상 파일, diff, 로그, URL, 문서, 이슈 또는 저장소 범위 → [작업 대상]
- `constraints`: 수정 범위, 금지사항, 스타일, 호환성 조건, 제외 범위 → [제약사항]
- `verification` (required): 테스트, lint, 빌드, 수동 확인 등 완료 여부를 판단할 기준 → [검증 기준]
- `output_format` (required): 결과 응답에 포함해야 할 섹션과 형식 → [출력 형식]

## Better prompt templates

### Minimal

```text
Turn repository information into a clear, attractive, accurate infographic plan. 대상은 [작업 대상]입니다. 완료 후 README에서 확인한 사실만 핵심 수치로 사용한다.; 텍스트가 이미지에서 읽기 쉬운 길이인지 확인한다. 기준으로 확인하고 Deliverable, Inputs used, Key decisions, Validation, Follow-ups 형식으로 요약해줘.
```

### High-signal

```text
Turn repository information into a clear, attractive, accurate infographic plan.

대상:
- [작업 대상]

제약:
- [수정 범위와 금지사항]
- 확인하지 않은 사실은 단정하지 않기

절차:
1. 먼저 목표, 입력, 현재 상태를 확인해줘.
2. 필요한 최소 범위로 작업해줘.
3. README에서 확인한 사실만 핵심 수치로 사용한다.; 텍스트가 이미지에서 읽기 쉬운 길이인지 확인한다. 기준으로 검증해줘.
4. 실패나 불확실성이 있으면 원인과 후속 조치를 적어줘.

출력:
- Deliverable, Inputs used, Key decisions, Validation, Follow-ups
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

- Overall: 78
- intent_clarity: 90
- input_specificity: 55
- constraint_clarity: 75
- workflow_reusability: 80
- verification_strength: 70
- output_specificity: 85
- generalization_safety: 88

## Install readiness

- Grade: review_recommended
- Recommendation: preview에서 변수/검증 기준을 확인한 뒤 promote하세요.
- Blocker: 작업 대상 신호가 부족합니다.

### Diagnostics

- 입력 대상이 예시에서 충분히 명확하지 않습니다.

## Evidence

- GitHub 저장소 분석해서 16:9 인포그래픽 이미지 프롬프트 만들어줘
- 레포 분석 후 상세하고 간략한 스타일 적용 인포그래픽 설계
