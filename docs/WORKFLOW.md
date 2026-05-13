# 보수적 개발 워크플로

## 원칙

기능 하나, 버그 하나, 문서 정리 하나, 인프라 변경 하나는 PR 하나로 끝냅니다.

무관한 작업을 묶지 않습니다. 여러 subsystem을 건드리는 일이면, 함께 배포되어야 앱이 동작하는 경우를 제외하고 나눕니다.

## 작업 순서

1. `docs/CONTEXT.md`, `docs/CURRENT_HANDOFF.md`, `docs/PROJECT_BRIEF.md`, `docs/TASKS.md`를 읽습니다.
2. `docs/GIT_CONVENTION.md`의 제목, 라벨, 크기 규칙을 확인합니다.
3. 작업이 크거나 병렬화될 수 있으면 `docs/work-units/`에 짧은 작업 단위 문서를 직접 추가합니다.
4. 해당 작업만 구현합니다.
5. 관련 검증을 실행합니다.
6. 필요하면 `docs/CURRENT_HANDOFF.md`와 `docs/TASKS.md`를 갱신합니다.
7. `codex/<작업명>` 브랜치를 push하고 PR을 엽니다.
8. GitHub 라벨을 붙이고 CI를 확인합니다.
9. CI가 통과하면 squash merge하고 브랜치를 삭제합니다.

## PR 크기 기준

- 선호: 5개 파일 이하
- 허용: 10개 파일 이하
- 11개 이상: 원칙적으로 나눕니다
- 예외: 초기 bootstrap, schema와 코드가 반드시 함께 가야 하는 작은 계약 변경

## 브랜치 이름

형식:

```text
codex/<short-task-name>
```

예시:

- `codex/crawler-parser-hardening`
- `codex/add-ci`
- `codex/instrument-master-import`

## PR에 반드시 포함할 내용

- 한국어 요약
- `[타입][영역]` 제목
- 타입/영역/크기 라벨
- 검증 명령과 결과
- 남은 리스크
- 후속 작업
