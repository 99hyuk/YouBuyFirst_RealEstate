# 에이전트 작업 가이드

이 저장소는 너나사 (YouBuyFirst) 최종 제품을 단계적으로 구현합니다. `main`에 올라간 현재 실행 기반은 커뮤니티 크롤링/감성 ingestion MVP이고, 이후 작업은 `docs/workstreams/`의 병렬 트랙 단위로 나눠 진행합니다.

## 제품 목표

너나사 (YouBuyFirst)는 커뮤니티 심리, 종목별 언급량, 시세/호가, 모의투자 에이전트를 결합해 “개미 심리를 읽는 투자 참고 서비스”를 만드는 프로젝트입니다.

현재 구현된 기반은 네이버 종토방과 에펨코리아 주식 게시판에서 신규 글을 수집하고, 국내 주식과 미국 상장 주식/ETF 언급을 인식한 뒤, 각 언급을 `bullish`, `bearish`, `neutral`로 분류해 Spring Boot 백엔드에 저장하는 ingestion 파이프라인입니다.

새 채팅에서 맡는 일은 전체 제품 중 하나의 트랙입니다. 먼저 사용자의 요청이 어느 트랙인지 정하고, 해당 트랙 문서를 읽은 뒤 그 범위 안에서만 작업합니다.

## 현재 아키텍처

- `backend/`: Spring Boot 3.3, Java 21, JPA, Flyway, MySQL, Swagger
- `pipeline/`: Python pipeline, APScheduler, HTTPX, BeautifulSoup, Playwright fallback, OpenAI provider abstraction
- `docker-compose.yml`: local MySQL + backend + pipeline runtime

## 범위 제한

- 담당 트랙과 명시 요청 없이 OCR 자산 연동, 실거래, 로그인/보안, 운영 배포를 추가하지 않습니다.
- 프론트 작업은 `front` 트랙에서만 진행합니다.
- 시세 작업은 `market`, 모의투자는 `trade`, AI 전략 에이전트는 `agent` 트랙에서만 진행합니다.
- CAPTCHA 우회, 로그인 세션 크롤링, 프록시 회전, fingerprint 위장은 하지 않습니다.
- 공개 HTTP 수집을 우선하고, Playwright는 렌더링 fallback으로만 사용합니다.
- 저장 원문은 제목, 본문 일부, URL, 작성자 해시, 작성 시각, 원문 해시로 제한합니다.

## 협업과 도구 사용 원칙

- Codex는 사용자의 요구를 무조건 수용하지 않습니다. 모순, 리스크, 더 나은 대안이 보이면 질문하거나 반박합니다.
- Superpowers는 기획, 설계, 구현 계획, 검증, 디버깅 게이트로 사용합니다.
- gstack은 브라우저 QA, 시각 확인, 성능/품질 검증처럼 실제 확인 가치가 있을 때 사용합니다.
- 개발/운영 문제 해결, 성능 개선, 품질 개선, 기술 의사결정은 `docs/ENGINEERING_EVIDENCE_GUIDE.md` 기준으로 Notion 기술 경험 기록 DB에 남깁니다.
- Notion 루트나 Archive 페이지를 `replace_content`로 수정할 때는 child page/database 보존 여부를 먼저 확인합니다. `allow_deleting_content`는 링크 블록을 실제 삭제할 수 있으므로, 단순 레이아웃 정리에는 쓰지 않습니다.

## Notion 구조 변경 게이트

Notion 루트, 홈카드, 주요 DB 페이지, 제품 기획, 작업 진행, 개발자 기술 경험, 에이전트 운영 로그, Archive를 바꾸는 작업은 일반 문서 수정이 아니라 사용자용 정보 구조 변경으로 취급합니다.

- 변경 전 현재 페이지를 fetch하고 child page/database 링크를 확인합니다.
- 사용자용 화면 개선인지, 에이전트 운영 규칙 정리인지 먼저 분리합니다.
- 큰 구조 변경은 바로 적용하지 않고 후보 구조를 설명하거나 별도 후보 페이지/작은 섹션 변경으로 진행합니다.
- `replace_content`는 최후 수단입니다. 가능한 한 작은 섹션 단위로 수정합니다.
- 제품 기획에는 PR 이력이나 운영 사고를 섞지 않습니다. 작업 이력은 작업 로그/Archive, 운영 사고는 에이전트 운영 로그에 둡니다.
- 홈카드와 DB 페이지는 전체 DB를 먼저 펼치기보다 필터된 보기, 대표 보기, 이동 링크를 우선합니다.
- 변경 후 루트와 핵심 카드 2개 이상을 다시 확인해 사람이 탐색하기 쉬운지 검증합니다.
- 이 규칙을 어기거나 사용자가 UI 회귀를 지적하면 에이전트 운영 로그에 원인과 재발 방지를 남깁니다.

## 검증 명령

Backend:

```bash
docker run --rm -v "${PWD}/backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn clean test
```

Pipeline:

```bash
docker run --rm -v "${PWD}/pipeline:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] && pytest"
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

작업 하나는 브랜치 하나와 PR 하나로 처리합니다. 기능 하나, 버그 하나, 문서 정리 하나, CI/runtime 설정 변경 하나를 한 PR에 담습니다.

```text
codex/<short-task-name>
```

병렬 작업은 `docs/workstreams/README.md`의 일곱 트랙 중 하나로 구분합니다.

- `crawl`: 커뮤니티 글 수집, 소스 어댑터, 종목별 게시판 타깃, 수집 정책
- `data`: 종목 인식, 별칭 매칭, 감성 분류, 열기 지수, 30분 집계
- `market`: 실시간/지연 시세, 호가, quote cache, WebSocket
- `trade`: 가상 계좌, 주문, 체결, 포트폴리오, 수익률
- `agent`: AI 매매 판단, 커뮤니티별 성과 비교, 페르소나, 결정 로그
- `front`: 사용자 대시보드, UI 상태, mock data, API 연동, 차트
- `ops`: 기획 조율, 문서, Notion, PR/CI, 배포 정책

다른 채팅에서 작업을 시작하면 담당 트랙 문서를 먼저 읽고, 가능하면 해당 트랙 파일만 수정합니다.
PR에는 담당 트랙에 맞는 작업 트랙 `track:*` 라벨을 붙이고, Notion 작업 카드에도 `트랙` 값을 채웁니다.
작업 타입은 `type:*` 라벨로 표시합니다. 실제로 건드린 부분은 `part:*` 라벨과 Notion `변경 파트` 값으로 표시하되, 필요할 때만 붙입니다.
프론트 작업은 `front` 트랙으로 처리하고, `track:front` 라벨을 붙입니다. 화면 파일을 직접 바꾸면 `part:front`도 함께 붙입니다.
시세, 모의투자, AI 에이전트 작업은 각각 `market`, `trade`, `agent`로 나눕니다. 같은 PR에 섞지 않습니다.
의존이 적은 작업은 단위 테스트 후 `main`으로 바로 PR을 보냅니다. 결합이 강한 작업만 짧은 수명의 `track/*` 브랜치에서 통합 테스트 후 `main`으로 보냅니다.

PR을 열기 전:

1. `docs/CONTEXT.md`를 읽습니다.
2. `docs/CURRENT_HANDOFF.md`를 읽습니다.
3. `docs/DOCUMENTATION_GUIDE.md`에서 매번 읽을 문서와 검색용 기록을 구분합니다.
4. `docs/GIT_CONVENTION.md`를 읽습니다.
5. `docs/LABEL_GUIDE.md`에서 GitHub 라벨과 Notion 태그 의미를 확인합니다.
6. 병렬 작업이면 `docs/workstreams/README.md`와 담당 트랙 문서를 읽습니다.
7. 문제가 발생했거나 반복될 가능성이 있으면 `docs/TROUBLESHOOTING_GUIDE.md`를 읽고 Notion 기술 경험 기록 DB의 `문제해결` 유형으로 기록합니다.
8. 필요한 경우 `docs/work-units/`에 작업 단위 문서를 만들거나 갱신합니다.
9. 관련 테스트를 실행합니다.
10. 작업 상태나 범위가 바뀌면 `docs/CURRENT_HANDOFF.md`와 `docs/TASKS.md`를 갱신합니다.
11. `git`과 `gh`로 직접 push, PR 생성, 라벨 지정, CI 확인을 수행합니다.
12. 한국어 PR 본문은 PowerShell 파이프나 stdin으로 `gh`에 넘기지 않고, UTF-8 no BOM 파일을 만든 뒤 `--body-file <path>`로 전달합니다.
13. PR 생성/수정 직후 `gh pr view --json body --jq .body`로 본문이 깨지지 않았는지 확인하고, `??` 치환 문자열이 보이면 즉시 고칩니다.

무관한 backend, pipeline, runtime, ops 범위 변경을 한 PR에 섞지 않습니다.

PR 제목은 `[트랙][타입] 명사형 요약`으로 씁니다. 예: `[ops][docs] 에이전트 가이드와 PR 문장 정리`. `~한다`, `~했다`, `~함`처럼 동사형이나 축약형으로 끝내지 않습니다.

PR 본문과 Notion 작업 카드는 같은 카드형 흐름으로 씁니다: 한눈에 보기, 바뀐 내용, 리뷰 가이드, PR 범위, 검증 결과, 리스크와 후속 작업, Notion 기록, 라벨/태그 참고. 검증은 명령어보다 사람이 읽기 쉬운 결과를 먼저 적습니다.

기술 경험 기록은 작업일지보다 자세히 남깁니다. CI, Docker, GitHub, Notion, 외부 API, 인증, 환경 변수처럼 반복 가능성이 있는 문제는 Notion 기술 경험 기록 DB의 `문제해결` 유형에 `증상`, `발생 맥락`, `조사 과정`, `원인`, `해결`, `검증`, `재발 방지`를 카드형으로 기록합니다. 성능 개선, 품질 개선, 기술 결정은 `docs/ENGINEERING_EVIDENCE_GUIDE.md` 기준으로 별도 종류를 선택합니다.

## 참고 문서

- 최종 제품 기획: `docs/FINAL_PRODUCT_PLAN.md`
- 현재 MVP 범위: `docs/PROJECT_BRIEF.md`
- 현재 인수인계 상태: `docs/CURRENT_HANDOFF.md`
- 문서 구조와 읽기 우선순위: `docs/DOCUMENTATION_GUIDE.md`
- 기술 경험 기록 기준: `docs/ENGINEERING_EVIDENCE_GUIDE.md`
- 트러블슈팅 기록 기준: `docs/TROUBLESHOOTING_GUIDE.md`
- 크롤링/공개 배포 리스크 사례: `docs/LEGAL_RISK_CASES.md`
- 라벨/태그 사전: `docs/LABEL_GUIDE.md`
- 병렬 작업 트랙: `docs/workstreams/README.md`
- Git/PR 컨벤션: `docs/GIT_CONVENTION.md`
- 작업 방식: `docs/WORKFLOW.md`
