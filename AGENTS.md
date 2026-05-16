# 에이전트 작업 가이드

너나사 (YouBuyFirst)는 커뮤니티 글 수집, 종목 언급 인식, 반응 방향 분류, Spring Boot 저장까지 이어진 ingestion MVP를 기반으로 최종 제품을 트랙별로 구현합니다.

제품 목표는 커뮤니티 반응, 종목별 언급량, 시세/호가, 모의투자 에이전트를 결합해 "개미들의 투자 반응을 읽는 참고 서비스"를 만드는 것입니다. 실제 투자 자문, 실거래 지시, 수익 보장, 개인화 투자 권유처럼 보이는 기능과 표현은 피합니다.

## 시작 원칙

- `crawl 작업`, `front 작업`, `ops로 Notion 정리`처럼 말하면 해당 트랙을 먼저 정합니다.
- 이미 대화에 주입된 긴 문서는 터미널로 다시 전문 출력하지 않습니다.
- `AGENTS.md`, `docs/CURRENT_HANDOFF.md`, `docs/DOCUMENTATION_GUIDE.md`는 필요한 섹션만 확인합니다.
- 트랙이 명확하면 담당 트랙 README를 우선 보고, 트랙 경계가 헷갈릴 때만 `docs/workstreams/README.md`를 봅니다.
- 제품 방향이 필요한 경우에만 `docs/FINAL_PRODUCT_PLAN.md`의 관련 섹션을 봅니다.
- 시작할 때 작업 트랙, 수정 대상, 기록 위치, 주요 위험을 짧게 선언합니다.
- 범위 없는 `뭐 해야 해?` 요청에는 바로 구현하지 말고 `docs/CHAT_START_GUIDE.md` 기준으로 트랙 선택을 돕습니다.

## 협업 원칙

Codex는 사용자의 요구를 무조건 수용하는 실행기가 아닙니다. 제품 목표, 법적/운영 리스크, 트랙 경계, 검증 가능성, 문서 보존 원칙과 충돌하면 먼저 질문하거나 반박합니다.

반박할 때는 전제나 위험, 그대로 진행할 때의 문제, 대안 1-2개, 사용자가 결정할 지점을 짧게 말합니다. 특히 공개 배포, 크롤링 정책, 약관/robots, Notion 구조 변경, DB/API 계약, 트랙 경계, PR/문서 보존, 투자 자문처럼 보이는 표현은 확인합니다.

## 아키텍처와 트랙

- `backend/`: Spring Boot 3.3, Java 21, JPA, Flyway, MySQL, Swagger
- `pipeline/`: Python, APScheduler, HTTPX, BeautifulSoup, Playwright fallback, OpenAI provider abstraction
- `front/`: Vue 3 + Vite + TypeScript mock 와이어프레임 shell
- `docker-compose.yml`: local MySQL + backend + pipeline runtime

| 트랙 | 담당 |
| --- | --- |
| `crawl` | 커뮤니티 글 수집, 소스 어댑터, 종목별 게시판 타깃, 수집 정책 |
| `data` | 종목 인식, 별칭 매칭, 반응 방향, 열기 지수, 30분 집계 |
| `market` | 실시간/지연 시세, 호가, quote cache, WebSocket |
| `trade` | 가상 계좌, 주문, 체결, 포트폴리오, 수익률 |
| `agent` | AI 매매 판단, 커뮤니티별 성과 비교, 페르소나, 결정 로그 |
| `front` | 대시보드, UI 상태, mock data, API 연동, 차트 |
| `ops` | 기획 조율, 문서, Notion, PR/CI, 배포 정책 |

한 PR은 한 트랙만 소유합니다. 다른 트랙 파일을 바꿔야 하면 계약 문서나 사용자 확인을 먼저 둡니다.

## 범위 제한

- 담당 트랙과 명시 요청 없이 OCR 자산 연동, 실거래, 로그인/보안, 운영 배포를 추가하지 않습니다.
- CAPTCHA 우회, 로그인 세션 크롤링, 프록시 회전, fingerprint 위장은 하지 않습니다.
- 공개 HTTP 수집을 우선하고, Playwright는 렌더링 fallback으로만 사용합니다.
- 저장 원문은 제목, 본문 일부, URL, 작성자 해시, 작성 시각, 원문 해시로 제한합니다.
- 사용자 화면에서는 `커뮤니티 반응`을 우선합니다. 단일 분석값은 `반응 방향`, 내부 후보 필드는 `reactionDirection`입니다.

## 도구와 컨텍스트 예산

- Superpowers는 기획, 설계, 구현 계획, 검증, 디버깅 게이트로 씁니다.
- gstack은 front/UI 변경처럼 실제 브라우저 확인 가치가 있을 때 씁니다.
- 스킬 문서는 필요한 상황에서만 읽고, 긴 스킬은 필요한 절차만 확인합니다.
- Browser, Figma, Stitch, gstack, Superpowers 같은 큰 스킬 문서는 전문 출력하지 않습니다. 필요한 경우 `-TotalCount 120` 안팎이나 관련 섹션 검색으로 시작하고, 같은 스킬을 한 세션에서 반복해서 읽지 않습니다.
- `docs/work-units/`, `docs/superpowers/`, Notion 작업 로그, 세션 로그, 브라우저 콘솔 전체는 시작 루틴이 아닙니다.
- `docs/superpowers/specs/`, `docs/superpowers/plans/`는 과거 설계/실행 archive입니다. front 복구나 현재 작업은 담당 트랙 handoff를 우선하고, 과거 근거가 필요할 때만 파일 1개와 키워드 1개로 좁혀 봅니다.
- 넓은 `rg`, 전체 로그/JSONL 출력, 전체 Notion page/database fetch, 콘솔/DOM 전문 출력은 금지합니다. 경로, 키워드, 출력량을 먼저 좁힙니다.
- 토큰 최적화는 필수 검증, PR/라벨, Notion/gstack 필요성 판단을 없애는 근거가 아닙니다.

## Notion 구조 변경 게이트

Notion 루트, 홈카드, 주요 DB 페이지, 제품 기획, 작업 진행, 기술 경험 기록, 에이전트 운영 로그, Archive 변경은 사용자용 정보 구조 변경입니다.

- 변경 전 대상 page/database와 child link 보존 여부를 확인합니다.
- 큰 구조 변경은 후보안이나 작은 섹션 단위로 진행합니다.
- `replace_content`와 `allow_deleting_content`는 최후 수단입니다.
- 제품 기획, 작업 로그, 기술 경험 기록, 에이전트 운영 로그의 목적을 섞지 않습니다.
- 변경 후 루트와 핵심 카드 2개 이상을 다시 확인합니다.

## Git/PR/검증

- 작업 하나는 브랜치 하나와 PR 하나로 처리합니다.
- 브랜치 이름은 기본 `codex/<short-task-name>`이고, 병렬 작업은 `.worktrees/<task>`에서 진행합니다.
- PR 제목은 `[트랙][타입] 명사형 요약`으로 씁니다.
- PR에는 `track:*`, `type:*`, `size:*` 라벨을 붙이고, 필요한 경우에만 `part:*`를 붙입니다.
- 한국어 PR 본문은 UTF-8 no BOM 파일과 `gh --body-file <path>`를 사용합니다.
- PR 생성/수정 직후 `gh pr view --json body --jq .body`와 `??` 검색으로 한글 깨짐을 확인합니다.
- 관련 테스트를 실행합니다. 문서만 바꿔도 `git diff --check`를 실행합니다.
- 세부 PR/라벨/본문 규칙은 `docs/GIT_CONVENTION.md`와 `docs/LABEL_GUIDE.md`의 관련 섹션만 확인합니다.

검증 명령은 `docs/WORKFLOW.md`의 관련 섹션을 봅니다.

## 기록 기준

- PR 본문과 Notion 작업 카드는 같은 카드형 흐름을 씁니다.
- Notion 작업일지는 PR별 요약 기록입니다.
- 제품 개발/운영 문제, 성능 개선, 품질 개선, 기술 결정은 개발자 기술 경험 DB에 남깁니다.
- Codex, Notion, GitHub PR, 문서 운영 사고는 에이전트 운영 로그 DB에 분리합니다.

## 참고 문서

- 현재 인수인계: `docs/CURRENT_HANDOFF.md`
- 문서 구조와 읽기 게이트: `docs/DOCUMENTATION_GUIDE.md`
- 채팅 시작: `docs/CHAT_START_GUIDE.md`
- 작업 방식: `docs/WORKFLOW.md`
- 병렬 트랙: `docs/workstreams/`
- Git/PR 컨벤션: `docs/GIT_CONVENTION.md`
- 라벨 사전: `docs/LABEL_GUIDE.md`
