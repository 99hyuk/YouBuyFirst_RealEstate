# Work Unit: Notion and PR UI Polish

## Goal

Notion과 GitHub PR을 B + A 하이브리드 정보 구조로 정리해, 새 채팅이나 병렬 에이전트가 프로젝트 상태와 작업 맥락을 빠르게 파악하게 한다.

## Scope

- Notion project hub를 command center 형태로 정리
- 작업일지와 트러블슈팅 페이지를 카드형 기록 구조로 정리
- GitHub PR 템플릿을 Notion 작업 카드와 같은 흐름으로 개선
- 운영 문서와 handoff에 새 기록 규칙 반영

## Out of Scope

- Notion database 생성
- GitHub Actions에서 Notion 자동 업데이트
- 코드/크롤러/backend/pipeline 기능 변경

## Verification

- `git diff --check`로 문서 공백 오류 확인
- Notion fetch로 hub와 핵심 child page가 새 구조를 포함하는지 확인
- GitHub Actions Backend/Pipeline 체크 확인

## Notes

이 변경은 문서 UX 개선이다. PR은 기능 변경이 없음을 분명히 설명하고, 검증 섹션에는 문서 검증과 Notion 반영 사실을 결과 중심으로 적는다.
