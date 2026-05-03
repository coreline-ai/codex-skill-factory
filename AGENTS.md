# AGENTS.md — Codex Prompt Skill Factory 작업 규칙

이 파일은 이 저장소에서 작업하는 모든 AI 에이전트와 개발자가 따라야 하는 최상위 프로젝트 규칙이다. 더 자세한 제품 문서는 `docs/codex_prompt_skill_factory_dev_doc.md`를 우선한다.

## 1. 고정 목적

- 프로젝트 제목은 **Codex Prompt Skill Factory**다.
- 목적은 **누구나 설치해서 Codex 프롬프트 사용 패턴을 로컬에서 수집·분석하고, 반복 요청을 Skill 후보로 제안하며, 사용자가 승인한 후보를 Codex가 바로 사용할 수 있는 Skill로 자동 생성·설치하는 installable CLI 제품**을 만드는 것이다.
- 이 저장소는 특정 예시용 Skill 하나를 만드는 프로젝트가 아니다.
- 모든 구현, 문서, 테스트, 리팩터링은 위 목적에 직접 기여해야 한다.

## 2. 현행 제품 상태

- 현재 v0.1.0 기준 Golden Path는 `init → inbox → promote → doctor/dashboard`다.
- 핵심 CLI 패키지는 `tools/codex-skill-factory` 아래에 있다.
- 실제 엔트리포인트는 `codex-skill-factory = skill_factory.cli:app`다.
- user scope는 `~/.codex`, project scope는 `--repo .` 또는 `--project`를 사용한다.
- Codex hooks는 `hook-user-prompt`, `hook-turn-stop`, `hook-post-tool-use` CLI 명령으로 연결한다.
- 생성 Skill은 승인 기반으로만 설치되어야 하며, 자동 활성화/무단 생성은 금지한다.

## 3. 절대 지켜야 할 원칙

- Local-first: 기본 동작에서 프롬프트/로그/후보를 외부 서버로 보내지 않는다.
- Approval-first: 사용자 승인 없이 `SKILL.md`를 생성하거나 활성화하지 않는다.
- Deterministic default: 외부 LLM/API를 필수 의존성으로 추가하지 않는다.
- No secret retention: hook 저장 전 secret redaction을 유지한다.
- Product UX first: 사용자용 기본 흐름은 `init`, `inbox`, `promote`, `dashboard`, `doctor` 중심으로 유지한다.
- Backward compatible advanced commands: `scan`, `report`, `preview`, `approve`, `ignore`, `unignore`, `review`, `enrich`, `create`, `analytics`는 깨지지 않아야 한다.

## 4. 명시적 비목표

- v1 범위에서 클라우드 동기화, 팀 SaaS, 원격 DB, 웹 서버를 만들지 않는다.
- VS Code Extension은 만들지 않는다. `.vscode/tasks.json`은 보조 기능이다.
- Codex 자체 코드나 외부 Codex 런타임을 수정하지 않는다.
- 특정 프로젝트/고객/파일명에 과적합된 Skill을 저장소에 커밋하지 않는다.
- `.codex/skills/`에는 `.gitkeep` 외 생성 Skill을 커밋하지 않는다.

## 5. 파일/모듈 책임

- `tools/codex-skill-factory/skill_factory/cli.py`: Typer CLI, Golden Path, hook config 생성, doctor.
- `hook_handlers.py`: Codex hook stdin payload 처리, redaction, jsonl 저장.
- `storage.py`: user/project scope 경로, JSON/JSONL IO.
- `rules.py`: 규칙 기반 후보 분류.
- `similarity.py`: 로컬 TF-IDF/코사인 유사도 후보 생성.
- `analytics.py`: 성공률, 반복 요청, 후보/Skill 지표.
- `spec_compiler.py`, `enrichment.py`, `quality.py`: Skill Spec, Prompt Contract, 품질 점수, 제안 생성.
- `approvals.py`: 후보 상태 전이.
- `dashboard.py`: 정적 HTML/JSON 대시보드.
- `templates/SKILL.md.j2`: 생성 Skill 본문 템플릿.
- `tests/`: 단위 테스트와 CLI 제품 플로우 테스트.
- `docs/codex_prompt_skill_factory_dev_doc.md`: 현행 최우선 제품 개발 문서.

## 6. 작업 시작 전 체크

- 먼저 `git status --short --branch`로 사용자의 미커밋 변경을 확인한다.
- 사용자의 기존 변경을 되돌리거나 덮어쓰지 않는다.
- 목적과 무관한 기능 확장 요청은 목적 기준으로 재해석하거나 범위 밖이라고 명시한다.
- 문서와 코드가 충돌하면 `docs/codex_prompt_skill_factory_dev_doc.md`와 이 파일을 기준으로 정합성을 맞춘다.

## 7. 구현 규칙

- Golden Path를 깨는 변경은 금지한다.
- `init`은 기존 사용자 설정을 안전하게 다뤄야 한다. hook/config를 덮어쓸 때는 merge/backup 정책을 고려한다.
- `inbox`는 non-interactive 모드를 유지해야 하며 CI를 block하면 안 된다.
- `promote`는 후보 승인, Skill 생성, 상태 갱신, 설치를 일관되게 처리해야 한다.
- `doctor`는 실패를 exit code로 드러내야 하며 `--json` structured output을 유지한다.
- hook은 raw payload 전체를 저장하지 말고 필요한 key만 저장한다.
- 새 의존성은 `pyproject.toml`에 명시하고 Local-first/Deterministic 원칙을 해치지 않아야 한다.

## 8. 테스트/검증 규칙

- 코드 변경 후 기본 검증을 실행한다.
- 권장 명령:
  - `cd tools/codex-skill-factory && uv run --extra dev python -m pytest -p no:cacheprovider`
  - `cd tools/codex-skill-factory && uv run --extra dev ruff check --no-cache skill_factory tests ../../.codex/hooks`
- packaging 변경 시 wheel build/install smoke를 추가로 확인한다.
- hook 변경 시 UserPromptSubmit, Stop, PostToolUse fixture를 모두 확인한다.
- secret redaction 회귀 테스트는 반드시 유지한다.
- 테스트 후 `.venv`, `build`, `dist`, `*.egg-info`, `uv.lock`, `__pycache__` 같은 생성물을 커밋하지 않는다.

## 9. 문서 규칙

- 사용자-facing 동작이 바뀌면 README와 `docs/codex_prompt_skill_factory_dev_doc.md`를 함께 갱신한다.
- 과거 `dev-plan/` 문서는 기록이다. 현행 범위 판단은 dev doc과 이 파일을 우선한다.
- 문서는 “특정 Skill 제작”이 아니라 “Skill Factory 제품” 관점으로 작성한다.
- 체크리스트를 `[x]`로 바꾸려면 실제 검증 근거가 있어야 한다.

## 10. Git/배포 규칙

- 커밋/푸시는 사용자가 명시적으로 요청했을 때 수행한다.
- 커밋 전 `git diff --stat`과 관련 테스트 결과를 확인한다.
- 원격은 `https://github.com/coreline-ai/codex-skill-factory.git`의 `main` 브랜치를 기준으로 한다.
- 릴리스 전 최소 조건은 Golden Path smoke, pytest, ruff, wheel install smoke 통과다.

## 11. 완료 보고 규칙

- 변경 파일, 핵심 변경, 검증 결과, 남은 리스크를 간단히 보고한다.
- 테스트를 실행하지 못했으면 실행하지 못한 이유를 명확히 적는다.
- “완료”라고 말하려면 목적 정합성, 테스트/검증, 문서 동기화 상태를 함께 확인한다.
