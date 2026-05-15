# 보수적 개발 워크플로

## 원칙

기능 하나, 버그 하나, 문서 정리 하나, CI/runtime 설정 변경 하나는 PR 하나로 끝냅니다.

무관한 작업을 묶지 않습니다. 여러 subsystem을 건드리는 일이면, 함께 배포되어야 앱이 동작하는 경우를 제외하고 나눕니다.

트랙 이름은 작업 관리 단위이고 코드 패키지는 도메인 단위입니다. 패키지 경계가 헷갈리면 `docs/DOMAIN_PACKAGE_GUIDE.md`를 먼저 확인합니다.

Codex는 사용자의 요구를 무조건 수용하지 않습니다. 모순, 리스크, 더 나은 대안이 보이면 구현을 시작하기 전에 질문하거나 반박합니다. 이 원칙은 친절함보다 우선하는 것이 아니라, 친절함을 실제 안전성과 품질로 연결하기 위한 기본값입니다.

## 작업 순서

1. `AGENTS.md`, `docs/CURRENT_HANDOFF.md`, `docs/DOCUMENTATION_GUIDE.md`를 읽습니다.
2. `docs/GIT_CONVENTION.md`와 `docs/LABEL_GUIDE.md`의 제목, 라벨, 크기 규칙을 확인합니다.
3. 병렬 작업이면 `docs/workstreams/README.md`와 담당 트랙 문서를 읽습니다.
4. 필요한 경우에만 `docs/FINAL_PRODUCT_PLAN.md`, `docs/PROJECT_BRIEF.md`, `docs/TASKS.md`를 추가로 읽습니다.
5. Notion 루트, 홈카드, 주요 DB 페이지, 제품 기획, 작업 진행, 기술 경험 기록, 에이전트 운영 로그, Archive를 바꾸는 작업이면 아래 `Notion 구조 변경 게이트`를 먼저 통과합니다.
6. 작업이 크거나 병렬화될 수 있으면 `docs/work-units/`에 짧은 작업 단위 문서를 직접 추가합니다.
7. 해당 작업만 구현합니다.
8. 관련 검증을 실행합니다.
9. 제품 개발/운영 문제가 발생했거나 반복될 수 있으면 `docs/TROUBLESHOOTING_GUIDE.md`를 기준으로 Notion `개발자 기술 경험 DB`의 `문제해결` 유형에 기록합니다. 성능/품질 개선이나 기술 결정은 `docs/ENGINEERING_EVIDENCE_GUIDE.md` 기준으로 남깁니다. Codex/Notion/PR/문서 운영 사고는 `에이전트 운영 로그 DB`에 분리해 남깁니다.
10. 필요하면 `docs/CURRENT_HANDOFF.md`와 `docs/TASKS.md`를 갱신합니다.
11. `codex/<작업명>` 브랜치를 push하고 PR을 엽니다. 한국어 PR 본문은 UTF-8 no BOM 파일을 `gh --body-file <path>`로 넘깁니다.
12. 작업 트랙 `track:*`, 작업 타입 `type:*`, 크기 `size:*` GitHub 라벨을 붙이고, 필요할 때만 변경 파트 `part:*` 라벨을 추가한 뒤 CI를 확인합니다.
13. `gh pr view --json body --jq .body`로 PR 본문이 깨지지 않았는지 확인합니다. `??` 치환 문자열이 보이면 merge 전에 고칩니다.
14. CI가 통과하면 squash merge하고 브랜치를 삭제합니다.
15. Notion 작업일지에 핵심 변경, 검증 결과, PR 링크, 다음 작업자 메모를 남깁니다.

## 문서 미준수 사고 분석 게이트

문서에 이미 있는 원칙을 따르지 않았거나 사용자가 그런 가능성을 지적하면, 작업을 계속 밀어붙이지 않습니다. 먼저 아래 질문에 답합니다.

1. 어떤 문서, 섹션, 원칙을 놓쳤는가?
2. 문서를 읽지 않은 문제인가, 읽었지만 해석을 잘못한 문제인가, 도구 실행 중 검증을 빠뜨린 문제인가?
3. 손상된 대상이 있는가? 예: Notion child page/database, PR 본문, git 변경, 작업 로그, 제품 기획 문서.
4. 복구가 필요한가, 보정만 하면 되는가, 사용자 확인이 필요한가?
5. 같은 사고를 막기 위해 repo 문서나 Notion 에이전트 운영 로그에 무엇을 남길 것인가?

이 게이트는 개발자 기술 경험 기록이 아니라 `에이전트 운영 로그 DB` 대상입니다. 다만 사고가 실제 제품 개발/운영 문제를 유발했다면 관련 PR이나 기술 경험 기록에도 링크를 남깁니다.

## 짧은 트랙 지시 처리

사용자는 새 채팅을 시작할 때 긴 역할 프롬프트를 매번 붙이지 않아도 됩니다. 사용자가 `crawl 작업`, `front 작업`, `ops로 Notion 정리`, `agent 트랙 맡아`처럼 트랙과 대략적인 일을 말하면 에이전트가 자동으로 역할 프롬프트를 확장합니다.

에이전트는 작업 시작 전에 아래 네 가지를 짧게 선언합니다.

- 작업 트랙: `crawl`, `data`, `market`, `trade`, `agent`, `front`, `ops` 중 하나
- 수정 대상: repo 파일, Notion, GitHub, 런타임, 프론트 화면 등
- 기록 위치: PR, Notion 작업 로그, 개발자 기술 경험 DB, 에이전트 운영 로그 DB 중 필요한 곳
- 주요 위험: child DB 보존, 트랙 경계, 인코딩, 테스트 범위, 외부 API 등

사용자 지시가 애매하면 바로 구현하지 말고, 추정한 트랙과 범위를 먼저 말한 뒤 필요한 최소 질문만 합니다.

사용자가 빈 채팅에서 `뭐 해야 해?`, `다음 뭐하지?`처럼 범위 없이 물으면 `docs/CHAT_START_GUIDE.md`를 기준으로 트랙 선택 안내를 먼저 합니다. 이 경우 에이전트가 임의로 구현 트랙을 고르지 않습니다.

## Notion 구조 변경 게이트

Notion의 사람용 화면은 단순 메모장이 아니라 프로젝트 탐색 UI입니다. 구조 변경은 아래 순서를 지킨 뒤 적용합니다.

1. 변경 전 대상 페이지를 fetch하고 기존 child page/database 링크를 확인합니다.
2. 사용자용 정보 구조 변경과 에이전트 운영 규칙 정리를 분리합니다.
3. 큰 변경은 바로 덮어쓰지 않고 후보 구조, 별도 후보 페이지, 작은 섹션 수정 중 하나로 시작합니다.
4. `replace_content`는 최후 수단으로 두고, 가능한 한 작은 섹션 단위로 수정합니다.
5. 제품 기획, 작업 로그, 기술 경험 기록, 에이전트 운영 로그의 목적을 섞지 않습니다.
6. 홈카드와 DB 페이지는 전체 DB보다 필터된 보기, 대표 보기, 이동 링크를 먼저 배치합니다.
7. 변경 후 루트와 핵심 카드 2개 이상을 다시 확인합니다.
8. 사용자가 UI 회귀나 정보 손실을 지적하면 에이전트 운영 로그에 원인과 재발 방지를 남깁니다.

## 정기 점검 책임

각 트랙 에이전트는 자기 작업의 PR과 Notion 작업 로그를 갱신합니다. `ops`는 주요 PR이 merge된 뒤 또는 사용자가 점검을 요청했을 때 아래 세 곳을 확인합니다.

- 루트 대시보드의 중요 이슈와 트랙별 진행판
- 제품 기획과 작업 맥락 페이지
- 다음 작업 DB와 최근 작업 로그

자동화가 필요하면 별도 heartbeat 또는 cron automation으로 만들되, 자동 점검이 없더라도 `ops` 작업자는 주요 기준 변경 후 수동으로 정합성을 확인합니다.

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
- `codex/stock-master-import`

트랙이 분명하면 브랜치 이름 앞부분에 트랙을 드러냅니다.

예시:

- `codex/crawl-naver-targets`
- `codex/data-alias-matcher`
- `codex/market-quote-cache`
- `codex/trade-order-domain`
- `codex/agent-contrarian-log`
- `codex/front-dashboard-shell`
- `codex/ops-track-names`

## 병렬 작업 트랙

여러 채팅에서 동시에 작업할 때는 아래 일곱 트랙 중 하나를 고릅니다.

- `crawl`: 커뮤니티 글 수집, 소스 어댑터, 종목별 게시판 타깃, 수집 정책
- `data`: 종목 인식, 별칭 매칭, 감성 분류, 열기 지수, 30분 집계
- `market`: 실시간/지연 시세, 호가, quote cache, WebSocket
- `trade`: 가상 계좌, 주문, 체결, 포트폴리오, 수익률
- `agent`: AI 매매 판단, 커뮤니티별 성과 비교, 페르소나, 결정 로그
- `front`: 사용자 대시보드, UI 상태, mock data, API 연동, 차트
- `ops`: 기획 조율, 문서, Notion, PR/CI, 배포 정책

각 트랙의 상세 범위와 파일 소유권은 `docs/workstreams/` 아래 문서를 따릅니다. 한 채팅은 가능한 한 한 트랙만 담당합니다.

프론트 작업은 `front` 트랙으로 시작합니다. 화면 골격과 mock 데이터 작업은 API 구현 전에도 진행할 수 있고, 실제 API 연결은 각 기능 트랙의 계약이 생긴 뒤 별도 PR로 진행합니다.

시세 수집은 `market`, 모의 체결은 `trade`, 에이전트 판단은 `agent`가 맡습니다. 기술 성격이 다르므로 같은 PR에 섞지 않습니다.

## 통합 브랜치 전략

기본은 `main`에 자주 통합하는 방식입니다.

- 의존이 적은 작업은 `codex/<prefix>-<task>` 브랜치에서 작업하고, 테스트 통과 후 `main`으로 PR을 보냅니다.
- 공통 계약 PR은 먼저 `main`에 넣어 다른 트랙이 같은 기준을 보게 합니다.
- 미완성 기능은 feature flag, mock mode, disabled default로 숨깁니다.

결합이 강한 작업만 짧은 수명의 `track/*` 브랜치를 씁니다.

- 예: `track/front-dashboard`, `track/market-quotes`
- 하위 PR은 해당 `track/*` 브랜치를 base로 보냅니다.
- `track/*` 브랜치는 2-4개 PR, 3-5일 안에 `main`으로 통합합니다.
- 통합 전에는 해당 트랙 테스트와 필요한 smoke test를 실행합니다.

트랙별 GitHub 라벨:

- `track:crawl`: `crawl`
- `track:data`: `data`
- `track:market`: `market`
- `track:trade`: `trade`
- `track:agent`: `agent`
- `track:front`: `front`
- `track:ops`: `ops`

## PR에 반드시 포함할 내용

- 한국어 요약
- `[트랙][타입] 명사형 요약` 제목
- 작업 트랙/작업 타입/크기 라벨
- 필요한 경우 변경 파트 라벨
- 리뷰 가이드
- 사람이 읽기 쉬운 검증 결과
- 남은 리스크
- 후속 작업
- Notion 기록 링크
- 라벨/태그 의미를 확인할 수 있는 `docs/LABEL_GUIDE.md` 링크

PR 본문은 PR #7 수준의 카드형 구조로 씁니다. 첫 화면에서 의도와 상태를 보고, 중간에서 변경 범위를 이해하고, 마지막에서 검증과 다음 작업을 확인할 수 있어야 합니다.

검증은 명령어 자체보다 확인한 사실을 먼저 씁니다. 예를 들어 "Backend Docker test 통과, 2 tests"처럼 결과를 요약하고, 실제 명령어는 PR 본문의 접힌 영역이나 보조 설명에 둡니다.

Windows PowerShell에서 한국어 본문을 `gh`에 파이프로 전달하면 글자가 `??`로 저장될 수 있습니다. PR 생성/수정은 UTF-8 no BOM 파일과 `--body-file <path>`를 사용하고, 생성 직후 `gh pr view --json body --jq .body`로 확인합니다.

## Notion 기록

- Project hub: https://www.notion.so/35fdf321bd89809b87e4fc8eae4c2e77
- Archive & Admin: https://www.notion.so/360df321bd8981a6a60df71bca8bad5d
- 제품 기획과 작업 맥락: https://www.notion.so/360df321bd89815c9767e703058990db
- 작업 로그 DB data source: `collection://be609137-1bd8-4b22-989e-a987a8185135`
- 개발자 기술 경험 DB data source: `collection://7f052514-c585-4621-ad28-b54bb2eac5a8`
- 에이전트 운영 로그 DB data source: `collection://8646042e-8ea0-4dd5-a056-c01a8ec096ec`
- 다음 작업 DB data source: `collection://ecdda994-6376-489d-bd83-4cfbadb6de70`
- GitHub PR 운영 메모: https://www.notion.so/35fdf321bd89815c9808ff01a683f4bc

Notion은 B + A 하이브리드 구조를 씁니다. 프로젝트 허브는 현재 상태를 빠르게 보는 command center 역할을 하고, 작업일지는 작업 로그 DB에 남기는 PR별 카드형 기록을 뜻합니다.

Notion 작업일지는 PR 본문과 같은 카드형 흐름을 따릅니다. 작업 요약, 변경 범위, 검증 결과, PR 링크, 다음 작업자 메모를 시각적으로 구분해 남기고, 트랙 아이콘과 `트랙` 속성으로 병렬 작업 단위를 바로 알아볼 수 있게 합니다.

작업일지는 “무엇을 했는가”를 남기는 PR 카드입니다. 개발자 기술 경험은 “왜 어려웠고, 어떻게 판단했으며, 어떤 근거로 개선됐는가”를 남기는 포트폴리오 근거입니다. 에이전트 운영 로그는 Codex/Notion/GitHub/PR/문서 운영 사고와 재발 방지를 따로 남기는 공간입니다.

개발자 기술 경험은 작업일지보다 깊게 씁니다. 제품 개발/운영 문제를 조사했거나, 성능/품질을 개선했거나, 중요한 기술 결정을 내렸다면 Notion `개발자 기술 경험 DB`에 `문제해결`, `성능개선`, `품질개선`, `기술결정` 중 하나로 남깁니다. 에이전트/도구 운영 사고는 Notion `에이전트 운영 로그 DB`에 남깁니다. 작성 구조는 `docs/ENGINEERING_EVIDENCE_GUIDE.md`와 `docs/TROUBLESHOOTING_GUIDE.md`를 함께 봅니다.

## 문서 길이 관리

문서 구조와 읽기 우선순위는 `docs/DOCUMENTATION_GUIDE.md`를 따릅니다. 새 채팅은 모든 문서를 읽지 않습니다. 먼저 `AGENTS.md`, `CURRENT_HANDOFF.md`, `DOCUMENTATION_GUIDE.md`, 담당 트랙 문서를 읽고, 나머지는 필요한 키워드로 검색합니다.
