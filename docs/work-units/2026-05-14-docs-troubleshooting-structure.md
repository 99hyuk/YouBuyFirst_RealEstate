# 작업 단위: 문서 구조와 트러블슈팅 기록 기준 정리

## 목적

작업 문서가 계속 길어지면서 새 채팅의 컨텍스트를 과하게 쓰는 문제를 줄이고, 트러블슈팅은 오히려 더 자세하고 보기 좋게 남기도록 기준을 분리합니다.

## 포함 범위

- `docs/DOCUMENTATION_GUIDE.md` 추가
- `docs/TROUBLESHOOTING_GUIDE.md` 추가
- `docs/archive/README.md` 추가
- `AGENTS.md`, `WORKFLOW.md`, `CURRENT_HANDOFF.md`에 문서 계층과 트러블슈팅 기록 규칙 반영
- Notion 기술 경험 기록 DB의 `문제해결` 유형에 카드형 템플릿 기준 추가

## 제외 범위

- 기존 완료 작업 대량 이동
- Notion DB schema 변경
- backend, pipeline, front 기능 구현

## 검증 기준

- 새 에이전트가 매번 읽을 문서와 검색용 기록 문서를 구분할 수 있습니다.
- 문제 발생 시 Notion 기술 경험 기록 DB에 남길 상세 템플릿을 확인할 수 있습니다.
- `git diff --check`가 통과합니다.
