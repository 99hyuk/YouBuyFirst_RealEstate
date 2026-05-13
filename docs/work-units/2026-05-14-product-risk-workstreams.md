# 작업 단위: 제품 기획, 크롤링 리스크, 병렬 트랙 정리

## 목적

최종 기획에 커뮤니티별 수익률 비교 에이전트와 시세 중심 투자 참고 화면을 반영하고, 크롤링/공개 배포 리스크와 병렬 작업 기준을 다음 에이전트가 바로 참고할 수 있게 문서화합니다.

## 범위

- `docs/FINAL_PRODUCT_PLAN.md` 재정리
- `docs/LEGAL_RISK_CASES.md` 추가
- `docs/workstreams/` 작업 트랙 문서 추가
- `AGENTS.md`, `docs/CONTEXT.md`, `docs/CURRENT_HANDOFF.md`, `docs/PROJECT_BRIEF.md`, `docs/TASKS.md`, `docs/WORKFLOW.md`, `docs/GIT_CONVENTION.md`의 참조 갱신
- Superpowers 설계 문서 추가

## 제외

- crawler/parser 구현
- 시세 provider 구현
- 모의투자/에이전트 코드 구현
- Notion 데이터베이스 구조 변경

## 검증 기준

- 문서 경로와 링크가 실제 파일과 맞습니다.
- `git diff --check`가 통과합니다.
- PR 본문에 변경 범위, 리스크, 다음 작업자 메모를 한국어로 남깁니다.

## 다음 작업자 메모

다른 채팅에서 병렬 작업을 시작할 때는 `docs/workstreams/README.md`에서 트랙을 고르고, 해당 트랙 README를 먼저 읽습니다. 구현 PR은 이 문서 PR과 섞지 않습니다.
