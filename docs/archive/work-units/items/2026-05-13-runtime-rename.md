# Work Unit: Runtime Identifier Rename

## Goal

문서에 반영된 새 프로젝트명 `너나사 (YouBuyFirst)`와 코드/설정의 런타임 식별자를 일치시킨다.

## Scope

- Java 패키지명을 `com.youbuyfirst`로 변경
- Spring Boot 애플리케이션 클래스를 `YouBuyFirstApplication`으로 변경
- Python pipeline 패키지명을 `youbuyfirst_pipeline`로 변경
- Docker Compose, Spring datasource, MySQL DB/user/password, Docker 이미지/JAR 이름을 `youbuyfirst` 기준으로 변경
- CI와 로컬 검증 명령을 stale target 영향을 받지 않도록 `mvn clean test`로 조정

## Out of Scope

- 크롤러 파싱 로직 개선
- 반응 방향 분석 품질 개선
- 대시보드, OCR, 모의투자, 인증/인가

## Verification

- Backend Docker test: `mvn clean test`
- Pipeline Docker test: `pip install -e .[test] && pytest`
- Docker Compose smoke test: MySQL, backend, pipeline 기동 확인
- 옛 프로젝트명/패키지명 식별자 검색

## Notes

이 PR은 rename 특성상 파일 수가 많지만 기능 변경은 포함하지 않는다. 이후 작업자는 `AGENTS.md`, `docs/CURRENT_HANDOFF.md`, `docs/TASKS.md`를 기준으로 `YouBuyFirst` 런타임 이름을 사용한다.
