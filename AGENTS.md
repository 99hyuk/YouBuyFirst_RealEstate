# 에이전트 작업 가이드

이 저장소는 너나사 (YouBuyFirst) MVP를 구현합니다. 현재 범위는 커뮤니티 크롤링과 감성 ingestion 파이프라인입니다.

## 제품 목표

네이버 종토방과 에펨코리아 주식 게시판에서 신규 글을 수집하고, 국내 주식과 미국 상장 주식/ETF 언급을 인식한 뒤, 각 언급을 `bullish`, `bearish`, `neutral`로 분류해 Spring Boot 백엔드에 저장합니다.

## 현재 아키텍처

- `backend/`: Spring Boot 3.3, Java 21, JPA, Flyway, MySQL, Swagger
- `worker/`: Python worker, APScheduler, HTTPX, BeautifulSoup, Playwright fallback, OpenAI provider abstraction
- `docker-compose.yml`: local MySQL + backend + worker runtime

## 범위 제한

- 명시 요청 없이 dashboard UI, OCR 자산 연동, 실거래, 로그인/보안을 추가하지 않습니다.
- CAPTCHA 우회, 로그인 세션 크롤링, 프록시 회전, fingerprint 위장은 하지 않습니다.
- 공개 HTTP 수집을 우선하고, Playwright는 렌더링 fallback으로만 사용합니다.
- 저장 원문은 제목, 본문 일부, URL, 작성자 해시, 작성 시각, 원문 해시로 제한합니다.

## 검증 명령

Backend:

```bash
docker run --rm -v "${PWD}/backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn test
```

Worker:

```bash
docker run --rm -v "${PWD}/worker:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] && pytest"
```

Local app:

```bash
docker compose up --build -d
docker compose ps
```

Swagger:

```text
http://localhost:8080/swagger-ui.html
```

## 브랜치와 PR 규칙

작업 하나는 브랜치 하나와 PR 하나로 처리합니다. 기능 하나, 버그 하나, 문서 정리 하나, 인프라 변경 하나를 한 PR에 담습니다.

```text
codex/<short-task-name>
```

PR을 열기 전:

1. `docs/CONTEXT.md`를 읽습니다.
2. `docs/CURRENT_HANDOFF.md`를 읽습니다.
3. `docs/GIT_CONVENTION.md`를 읽습니다.
4. 필요한 경우 `docs/work-units/`에 작업 단위 문서를 만들거나 갱신합니다.
5. 관련 테스트를 실행합니다.
6. 작업 상태나 범위가 바뀌면 `docs/CURRENT_HANDOFF.md`와 `docs/TASKS.md`를 갱신합니다.
7. `git`과 `gh`로 직접 push, PR 생성, 라벨 지정, CI 확인을 수행합니다.

무관한 backend, worker, infra, product-scope 변경을 한 PR에 섞지 않습니다.

## 참고 문서

- 최종 제품 기획: `docs/FINAL_PRODUCT_PLAN.md`
- 현재 MVP 범위: `docs/PROJECT_BRIEF.md`
- 현재 인수인계 상태: `docs/CURRENT_HANDOFF.md`
- Git/PR 컨벤션: `docs/GIT_CONVENTION.md`
- 작업 방식: `docs/WORKFLOW.md`
