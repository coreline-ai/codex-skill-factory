# Codex Skill Suggestions

## 1. `fix-failing-tests`

- 점수: 100
- 전체 빈도: 25
- 상태: pending_review
- 출처: rule
- Prompt 품질 점수: 89
- 주요 진단: Skill 생성을 위한 핵심 계약 정보가 충분합니다.
- 설치 준비도: install_recommended — 승인 후 바로 promote해도 좋습니다.

Use when the user asks to fix failing tests, CI failures, pytest/Jest errors, broken test suites, or red builds.

### 예시

- pytest 테스트 실패 고쳐줘. tests/test_api.py 타깃 테스트 재실행 필요
- failing test in pytest needs fix and root cause analysis
- CI 실패 red build야 broken test 원인 분석하고 최소 수정해줘
- jest failing test fix, reproduce the smallest failing case
- 테스트 깨졌어 pytest 로그 보고 원인 찾아 수정해줘

### 명령

```bash
codex-skill-factory preview fix-failing-tests
codex-skill-factory approve fix-failing-tests
codex-skill-factory ignore fix-failing-tests
codex-skill-factory create fix-failing-tests
```

## 2. `fix-lint-type-errors`

- 점수: 100
- 전체 빈도: 20
- 상태: pending_review
- 출처: rule
- Prompt 품질 점수: 83
- 주요 진단: 입력 대상이 예시에서 충분히 명확하지 않습니다.
- 설치 준비도: review_recommended — preview에서 변수/검증 기준을 확인한 뒤 promote하세요.

Use when the user asks to fix lint, formatting, typecheck, mypy, tsc, ruff, eslint, or static analysis errors.

### 예시

- ruff check 실패 lint 오류 수정해줘
- mypy 타입 에러와 typecheck 실패를 고쳐줘
- eslint prettier format 문제 정리해줘
- tsc 타입 오류 해결하고 동작 변경 없이 수정

### 명령

```bash
codex-skill-factory preview fix-lint-type-errors
codex-skill-factory approve fix-lint-type-errors
codex-skill-factory ignore fix-lint-type-errors
codex-skill-factory create fix-lint-type-errors
```

## 3. `repo-to-infographic`

- 점수: 100
- 전체 빈도: 10
- 상태: pending_review
- 출처: rule
- Prompt 품질 점수: 78
- 주요 진단: 입력 대상이 예시에서 충분히 명확하지 않습니다.
- 설치 준비도: review_recommended — preview에서 변수/검증 기준을 확인한 뒤 promote하세요.

Use when the user asks to analyze a GitHub repository and create a concise 16:9 infographic brief or image-generation prompt.

### 예시

- GitHub 저장소 분석해서 16:9 인포그래픽 이미지 프롬프트 만들어줘
- 레포 분석 후 상세하고 간략한 스타일 적용 인포그래픽 설계

### 명령

```bash
codex-skill-factory preview repo-to-infographic
codex-skill-factory approve repo-to-infographic
codex-skill-factory ignore repo-to-infographic
codex-skill-factory create repo-to-infographic
```

## 4. `review-current-diff`

- 점수: 100
- 전체 빈도: 20
- 상태: pending_review
- 출처: rule
- Prompt 품질 점수: 80
- 주요 진단: 수정 범위와 금지사항을 더 명확히 하는 것이 좋습니다.
- 설치 준비도: review_recommended — preview에서 변수/검증 기준을 확인한 뒤 promote하세요.

Use when the user asks to review the current git diff, PR changes, code changes, or wants risk and bug analysis before committing.

### 예시

- 현재 diff 리뷰하고 PR 전 위험 검토해줘
- review this current git diff before merge
- 변경사항 검토하고 누락 테스트와 회귀 위험 찾아줘
- PR 리뷰 관점으로 코드 리뷰 진행해줘

### 명령

```bash
codex-skill-factory preview review-current-diff
codex-skill-factory approve review-current-diff
codex-skill-factory ignore review-current-diff
codex-skill-factory create review-current-diff
```

## 5. `update-docs`

- 점수: 100
- 전체 빈도: 15
- 상태: pending_review
- 출처: rule
- Prompt 품질 점수: 77
- 주요 진단: 수정 범위와 금지사항을 더 명확히 하는 것이 좋습니다.
- 설치 준비도: review_recommended — preview에서 변수/검증 기준을 확인한 뒤 promote하세요.

Use when the user asks to update README, docs, API documentation, usage guides, or changelog-like documentation.

### 예시

- README 문서 업데이트하고 사용법 가이드 정리해줘
- docs documentation 사용법을 README에 추가하고 changelog 정리
- 문서 설명 추가하고 설치 실행 예시를 최신 상태로 맞춰줘

### 명령

```bash
codex-skill-factory preview update-docs
codex-skill-factory approve update-docs
codex-skill-factory ignore update-docs
codex-skill-factory create update-docs
```

## 6. `generate-release-notes`

- 점수: 100
- 전체 빈도: 10
- 상태: pending_review
- 출처: similarity
- Prompt 품질 점수: 85
- 주요 진단: Skill 생성을 위한 핵심 계약 정보가 충분합니다.
- 설치 준비도: install_recommended — 승인 후 바로 promote해도 좋습니다.
- 평균 유사도: 1.0
- 대표 토큰: release, notes, changes, from

Use when the user repeatedly asks to generate release notes from commits, diffs, PRs, or git changes (10 similar examples).

### 예시

- make version release notes based on commit history and user visible changes
- draft release communication using commit messages and upgrade notes
- write a release announcement from merged commits and categorize changes
- generate release summary from git commits with breaking changes and migration notes
- prepare release notes from current commits and summarize notable changes

### 명령

```bash
codex-skill-factory preview generate-release-notes
codex-skill-factory approve generate-release-notes
codex-skill-factory ignore generate-release-notes
codex-skill-factory create generate-release-notes
```
