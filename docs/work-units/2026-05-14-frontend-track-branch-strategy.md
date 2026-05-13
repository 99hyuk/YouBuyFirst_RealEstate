# 작업 단위: 프론트 독립 트랙과 하이브리드 브랜치 전략

## 목적

프론트 작업을 `product-planning-ops`에서 분리해 `frontend-experience` 독립 트랙으로 만들고, 의존도에 따라 `main`에 바로 통합할지 `track/*` 브랜치를 거칠지 판단하는 기준을 정합니다.

## 범위

- `frontend-experience` 트랙 문서 추가
- `product-ops-experience`를 `product-planning-ops`로 재정의
- `track:frontend` GitHub 라벨과 Notion 트랙 옵션 추가
- `main` 우선 통합과 짧은 `track/*` 브랜치 예외 전략 문서화
- AGENTS, CURRENT_HANDOFF, WORKFLOW, GIT_CONVENTION, TASKS 갱신

## 제외

- 프론트 프로젝트 생성
- 실제 UI 구현
- backend/worker 코드 변경
- track 브랜치 실제 생성

## 다음 작업자 메모

의존이 적은 작업은 `codex/<prefix>-<task>` 브랜치에서 작업해 테스트 후 `main`으로 바로 보냅니다. 결합이 강한 작업만 `track/*` 브랜치를 짧게 쓰고, 2-4개 PR 또는 3-5일 안에 `main`으로 통합합니다.
