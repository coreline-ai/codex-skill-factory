# Codex Prompt Skill Factory 문서 인덱스

> **프로젝트 제목:** Codex Prompt Skill Factory  
> **고정 목적:** 누구나 설치해서 Codex 프롬프트 사용 패턴을 로컬에서 수집·분석하고, 반복 요청을 Skill 후보로 제안하며, 사용자가 승인한 후보를 Codex가 바로 사용할 수 있는 Skill로 자동 생성·설치하는 installable CLI 제품.

## 읽는 순서

1. [`../AGENTS.md`](../AGENTS.md) — AI 에이전트와 개발자가 반드시 따라야 하는 프로젝트 목적/진행 규칙
2. [`codex_prompt_skill_factory_dev_doc.md`](codex_prompt_skill_factory_dev_doc.md) — 현행 제품 목표, UX, 아키텍처, 테스트 시나리오의 단일 기준 문서
3. [`codex_prompt_skill_factory_product_plan_expert_review.md`](codex_prompt_skill_factory_product_plan_expert_review.md) — 구현 전 전문가 리뷰와 리스크 잠금 사항
4. [`../dev-plan/`](../dev-plan/) — 과거 구현/계획 기록. 현행 제품 범위 판단에는 1~2번 문서를 우선한다.

## 문서 정리 기준

- 모든 문서는 **설치형 CLI 제품**이라는 목적을 기준으로 읽는다.
- 이 저장소에서 만드는 것은 특정 Skill 하나가 아니라, 사용자의 반복 프롬프트를 분석해 승인 기반으로 Skill을 생성·설치하는 도구다.
- 과거 계획 문서의 고도화 항목은 기록으로 유지하되, 현재 v1 범위는 `init → inbox → promote → doctor` 검증 흐름을 우선한다.
