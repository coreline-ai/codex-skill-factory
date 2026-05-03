# Codex Prompt Skill Factory

> **프로젝트 제목:** Codex Prompt Skill Factory  
> **고정 목적:** 누구나 설치해서 Codex 프롬프트 사용 패턴을 로컬에서 수집·분석하고, 반복 요청을 Skill 후보로 제안하며, 사용자가 승인한 후보를 Codex가 바로 사용할 수 있는 Skill로 자동 생성·설치하는 installable CLI 제품.

## 제품 목표

이 프로젝트는 특정 예시용 Skill을 만드는 프로젝트가 아니다. 목표는 사용자가 평소처럼 Codex를 쓰는 동안 반복되는 프롬프트 패턴을 로컬에서 분석하고, 재사용 가능한 Skill 후보를 제안한 뒤, 사용자가 승인한 후보만 실제 Codex Skill로 생성·설치하는 제품형 CLI를 완성하는 것이다.

## Golden Path

```text
codex-skill-factory init
(평소처럼 Codex 사용)
codex-skill-factory inbox
codex-skill-factory promote <candidate>
codex-skill-factory doctor
```

프로젝트 로컬로만 검증할 때는 아래처럼 실행한다.

```text
codex-skill-factory init --repo . --yes
codex-skill-factory inbox --repo . --no-interactive
codex-skill-factory promote <candidate> --repo . --yes
codex-skill-factory doctor --repo .
```

## 제품 원칙

| 원칙 | 의미 |
|---|---|
| Local-first | 프롬프트 로그와 후보 데이터는 기본적으로 사용자 로컬에 저장한다. |
| Approval-first | 사용자 승인 없이 Skill을 생성하거나 활성화하지 않는다. |
| Installable CLI | repo-local 스크립트가 아니라 누구나 설치 가능한 CLI 제품으로 만든다. |
| Deterministic default | 기본 분석은 외부 LLM/API 없이 재현 가능한 로컬 규칙으로 동작한다. |
| Product UX first | 사용자는 `init`, `inbox`, `promote`, `dashboard`, `doctor` 중심으로 사용한다. |

## 문서 기준

| 문서 | 역할 |
|---|---|
| [`docs/codex_prompt_skill_factory_dev_doc.md`](docs/codex_prompt_skill_factory_dev_doc.md) | 현재 기준의 제품형 개발 문서이자 최우선 기준 문서 |
| [`docs/codex_prompt_skill_factory_product_plan_expert_review.md`](docs/codex_prompt_skill_factory_product_plan_expert_review.md) | 제품 계획 전문가 리뷰와 구현 전 잠금 사항 |
| [`dev-plan/`](dev-plan/) | 과거 구현 단계별 기록. 현행 범위 판단은 개발 문서를 우선한다. |

## 현재 상태

- 제품 Golden Path: `init`, `inbox`, `promote`, `doctor` CLI가 구현되어 있다.
- 엔진 자산: hook, 로컬 저장, 후보 분석, 유사도 분석, analytics, approval 상태, enrichment, dashboard, Skill 렌더링 기반이 존재한다.
- hook 실행: `init`이 `codex-skill-factory hook-*` 명령을 Codex hook으로 연결한다.
- 저장 범위: 기본 user scope와 `--repo`/`--project` 기반 project scope를 지원한다.
- 검증: 단위/CLI 제품 플로우 테스트와 ruff 검사를 통과한다.
- 범위 고정: VS Code Extension, 서버, 원격 동기화, 외부 LLM/API 필수 의존성은 v1 목표가 아니다.
