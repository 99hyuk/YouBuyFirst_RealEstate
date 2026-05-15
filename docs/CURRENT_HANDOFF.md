# 현재 작업 인수인계

마지막 갱신: 2026-05-15

이 문서는 새 채팅, 병렬 에이전트, 또는 다음 작업자가 가장 먼저 읽는 요약입니다. 문서 읽기 우선순위는 `docs/DOCUMENTATION_GUIDE.md`를 기준으로 봅니다. 자세한 제품 방향은 `docs/FINAL_PRODUCT_PLAN.md`, 현재 MVP 범위는 `docs/PROJECT_BRIEF.md`, 작업 방식은 `docs/WORKFLOW.md`, 채팅 시작 방식은 `docs/CHAT_START_GUIDE.md`, Git/PR 규칙은 `docs/GIT_CONVENTION.md`를 기준으로 봅니다. 크롤링/공개 배포 리스크는 `docs/LEGAL_RISK_CASES.md`, 병렬 작업 트랙은 `docs/workstreams/README.md`를 기준으로 봅니다.

## 지금까지 한 일

- 너나사 (YouBuyFirst) MVP 저장소를 초기 구성했습니다.
- Spring Boot 백엔드, Python pipeline, MySQL, Docker Compose 기반 로컬 실행 구성을 만들었습니다.
- 네이버 종토방과 에펨코리아 게시글 수집, 종목 매칭, LLM provider 추상화, mock sentiment fallback, ingestion API, admin 조회 API를 구현했습니다.
- 제한 원문 저장 정책을 반영했습니다: 제목, 본문 일부, URL, 작성 시각, 작성자 표시명 해시, 원문 해시만 저장합니다.
- Swagger에서 crawl run, posts, stock metrics를 확인할 수 있게 했습니다.
- GitHub Actions CI와 PR 템플릿을 추가했습니다.
- 최종 기획안, MVP 범위, 작업 목록, 에이전트 인수인계 문서를 추가했습니다.
- 문서의 제품명은 `너나사 (YouBuyFirst)`로 정리했고, 런타임 식별자도 `com.youbuyfirst`, `youbuyfirst-pipeline`, `youbuyfirst` DB 이름 기준으로 맞췄습니다.
- 최종 기획에 커뮤니티별 수익률 비교 에이전트, 시세/호가 중심 투자 참고 화면, 소스별 수집 활성화 정책을 반영했습니다.
- 크롤링 분쟁 사례와 공개 배포 리스크를 별도 문서로 정리했습니다.
- 여러 채팅이 동시에 일할 수 있도록 일곱 개의 병렬 작업 트랙 문서를 추가했습니다.
- GitHub 라벨 체계를 `track:*`, `type:*`, `part:*`, `size:*`로 정리했습니다.
- Python 실행 단위 이름을 `worker`에서 `pipeline`으로 정리했습니다.

## 최근 결정

- 사용자용 PowerShell 스크립트는 두지 않습니다.
- PR 생성, 라벨 지정, CI 확인, merge는 Codex/에이전트가 `git`과 `gh`로 직접 처리합니다.
- PR 설명과 커밋 본문은 한국어로 작성합니다.
- PR 제목은 `[트랙][타입] 명사형 요약` 형식을 사용합니다. 예: `[ops][docs] 에이전트 가이드와 PR 문장 정리`. `~한다`, `~했다`, `~함`처럼 동사형이나 축약형으로 끝내지 않습니다.
- PR 본문은 PR #7처럼 카드형 구조로 씁니다. 검증 섹션에는 명령어 나열보다 사람이 읽을 수 있는 통과 결과와 확인 사실을 먼저 적습니다.
- 한국어 PR 본문은 PowerShell pipeline/stdin으로 `gh`에 넘기지 않습니다. UTF-8 no BOM 파일을 만들고 `gh --body-file <path>`를 사용한 뒤 저장된 본문을 확인합니다.
- PR 본문과 Notion 작업일지는 같은 카드 구조를 씁니다: 한눈에 보기, 변경 내용, PR 범위, 검증 결과, 리스크, 다음 에이전트 메모, 라벨/태그 참고.
- GitHub 라벨과 Notion 태그 의미는 `docs/LABEL_GUIDE.md`를 기준으로 봅니다.
- Notion 허브는 B + A 하이브리드 구조를 씁니다: 첫 화면은 command center, 세부 기록은 PR 카드 로그입니다.
- 문서는 길게 누적하지 않고 계층화합니다. 매번 읽는 문서와 검색용 기록은 `docs/DOCUMENTATION_GUIDE.md`를 기준으로 구분합니다.
- 개발자 기술 경험은 작업일지보다 자세히 기록합니다. 반복 가능성이 있는 제품 개발/운영 문제는 `docs/TROUBLESHOOTING_GUIDE.md` 구조로 Notion 개발자 기술 경험 DB의 `문제해결` 유형에 남깁니다. Codex/Notion/GitHub PR/문서 운영 사고는 에이전트 운영 로그 DB에 분리합니다.
- 너무 큰 PR을 피하기 위해 5개 파일 이하를 선호하고, 10개 파일을 넘으면 분리 가능성을 먼저 검토합니다.
- 30분 커뮤니티 집계는 제품 핵심으로 유지합니다.
- 공개 배포 시 원문 재게시, 작성자 추적, 닉네임 랭킹은 하지 않고 집계 지표와 AI 재서술 근거 중심으로 표시합니다.
- 소스별 상태는 `enabled`, `public-demo-only`, `local-research-only`, `disabled`로 나눕니다.
- 네이버/에펨코리아/디시/토스는 약관과 robots 정책 리스크가 있으므로 공개 운영 전에 소스별 검토가 필요합니다.
- 병렬 작업은 `crawl`, `data`, `market`, `trade`, `agent`, `front`, `ops` 일곱 트랙으로 나눕니다.
- 사용자가 `crawl 작업`, `front 작업`, `ops로 Notion 정리`처럼 짧게 말해도 에이전트가 긴 역할 프롬프트를 자동 확장합니다. 사용자가 매번 읽을 문서, 범위 제한, PR 규칙을 반복해서 말할 필요는 없습니다.
- 작업 시작 시 에이전트는 작업 트랙, 수정 대상, 기록 위치, 주요 위험을 스스로 짧게 선언합니다. 예: `작업 트랙: ops / 수정 대상: Notion / 기록 위치: 작업 로그 + 필요 시 에이전트 운영 로그 / 위험: child DB 보존`.
- 빈 채팅에서 사용자가 `뭐 해야 해?`, `다음 뭐하지?`처럼 물으면 바로 구현하지 않고 `docs/CHAT_START_GUIDE.md` 기준으로 트랙 설명과 가까운 다음 작업 후보를 보여준 뒤 트랙 선택을 돕습니다.
- 각 트랙 에이전트는 자기 PR과 작업 로그를 갱신합니다. `ops` 기획 에이전트는 루트 대시보드, 트랙별 진행판, 제품 기획과 작업 맥락을 주기적으로 점검하고 정리합니다.
- 병렬 작업 PR에는 `track:crawl`, `track:data`, `track:market`, `track:trade`, `track:agent`, `track:front`, `track:ops` 중 하나를 붙이고, Notion 작업 카드의 `트랙` 속성도 채웁니다.
- `type:*`는 작업 타입, `track:*`는 작업 트랙, `part:*`는 변경 파트입니다. `part:*`는 실제 파일이나 리뷰 경로를 드러낼 때만 붙이는 보조 라벨입니다.
- Notion 작업 로그와 다음 작업 DB에서는 같은 의미를 `변경 파트` 컬럼으로 기록합니다.
- 프론트 작업은 `front` 트랙으로 시작하고 `track:front` 라벨을 붙입니다. 화면 파일을 직접 바꾸면 `part:front`도 함께 붙입니다.
- 기획/조율/문서/Notion/PR 운영은 `ops` 트랙이 맡습니다.
- 시세 수집은 `market`, 모의 체결은 `trade`, AI 에이전트 판단은 `agent`가 맡습니다. 세 작업을 같은 PR에 섞지 않습니다.
- 의존이 적은 작업은 단위 테스트 후 `main`으로 바로 PR을 보냅니다. 결합이 강한 작업만 짧은 수명의 `track/*` 브랜치에서 통합 테스트 후 `main`으로 보냅니다.
- Notion의 현재 정본 기록 구조는 `개발자 기술 경험 DB`와 `에이전트 운영 로그 DB`로 분리합니다.
- 개발자 기술 경험은 `문제해결`, `성능개선`, `품질개선`, `기술결정`으로 구분합니다.
- 포트폴리오 후보는 `대표`, `보조`, `기록`으로 나누며, 단순 에이전트/도구 운영 이슈는 포트폴리오 경험처럼 쓰지 않고 에이전트 운영 로그에 둡니다.
- Notion 루트는 전체 DB를 inline으로 펼치지 않고, 최근 요약과 이동 링크만 둡니다.
- Notion 루트/Archive를 수정할 때 `allow_deleting_content`는 피합니다. child page/database 링크 블록을 삭제할 수 있어, 레이아웃 정리는 `update_content` 중심으로 합니다.
- Notion 루트, 홈카드, 주요 DB 페이지, 제품 기획, 작업 진행, 기술 경험 기록, 에이전트 운영 로그, Archive 변경은 사용자용 정보 구조 변경으로 취급합니다. 변경 전 fetch와 child link 확인, 사용자 UI와 운영 규칙 분리, 후보안 또는 작은 섹션 단위 변경, 변경 후 루트/핵심 카드 재확인을 거칩니다.
- 기존 Notion 원본 DB parent가 삭제 표시되어 새 Archive 아래에 작업 로그/기술 경험 기록/다음 작업 DB를 다시 만들었습니다. 새 작업은 현재 Notion 상태의 data source id만 사용합니다.

## 현재 GitHub 상태

- Repository: `99hyuk/YouBuyFirst`
- Default branch: `main`
- Bootstrap PR: https://github.com/99hyuk/YouBuyFirst/pull/1
- PR #1 상태: CI 통과 후 squash merge 완료
- GitHub labels: `track:*`, `type:*`, `size:*`, `part:*` 라벨 생성 완료
- 현재 작업 타입 라벨은 `feat`, `fix`, `docs`, `refactor`, `perf`, `chore`만 씁니다.
- 현재 checkout은 작업자별로 달라질 수 있으므로 `git status --short --branch`로 확인합니다.

## 현재 Notion 상태

- Project hub: https://www.notion.so/35fdf321bd89809b87e4fc8eae4c2e77
- Archive & Admin: https://www.notion.so/360df321bd8981a6a60df71bca8bad5d
- 제품 기획과 작업 맥락: https://www.notion.so/360df321bd89815c9767e703058990db
- 작업 로그 DB data source: `collection://be609137-1bd8-4b22-989e-a987a8185135`
- 개발자 기술 경험: https://www.notion.so/360df321bd89819aa871fe52c1a5cc56
- 개발자 기술 경험 DB data source: `collection://7f052514-c585-4621-ad28-b54bb2eac5a8`
- 에이전트 운영 로그: https://www.notion.so/360df321bd89818989d4f2de0d77da06
- 에이전트 운영 로그 DB data source: `collection://8646042e-8ea0-4dd5-a056-c01a8ec096ec`
- Legacy 기술 경험 기록 DB data source: `collection://95866ee7-17cb-412b-a9c8-80b1fde414dc`는 이전 구조 기록 확인용입니다. 새 기록의 정본으로 쓰지 않습니다.
- 다음 작업 DB data source: `collection://ecdda994-6376-489d-bd83-4cfbadb6de70`
- GitHub PR 운영 메모: https://www.notion.so/35fdf321bd89815c9808ff01a683f4bc
- 작업일지는 작업 로그 DB에 남기는 PR별 카드형 기록을 뜻합니다.
- 작업 로그 DB와 다음 작업 DB는 `변경 파트` 컬럼을 사용합니다.
- 작업이 끝나면 핵심 변경, 검증 결과, PR 링크, 다음 작업자 메모를 Notion 작업일지에 남깁니다.
- 제품 개발/운영 트러블슈팅은 개발자 기술 경험 DB의 `문제해결` 유형으로 남깁니다. 성능 개선, 품질 개선, 기술 결정은 `docs/ENGINEERING_EVIDENCE_GUIDE.md` 기준으로 종류와 포트폴리오 후보를 선택합니다. 에이전트/도구 운영 사고는 에이전트 운영 로그 DB에 남깁니다.

## 마지막 검증 기록

- Label/part/pipeline branch: Pipeline Docker test 통과, 4 tests
- Label/part/pipeline branch: Docker Compose config service가 `mysql`, `backend`, `pipeline`으로 출력됨
- Label/part/pipeline branch: GitHub labels가 `track:*`, `type:*`, `part:*`, `size:*` 체계로 정리됨
- Label/part/pipeline branch: Notion 라벨/태그 사전과 DB `변경 파트` schema 확인
- Label/part/pipeline branch: `git diff --check` 통과
- Runtime identifier rename branch: Backend Docker test 통과, 2 tests
- Runtime identifier rename branch: Pipeline Docker test 통과, 4 tests
- Runtime identifier rename branch: Docker Compose 기동 및 Swagger `200` 확인
- Runtime identifier rename branch: 옛 프로젝트명/패키지명 검색 결과 없음
- Runtime identifier rename branch: `git diff --check` 통과

## 다음 에이전트가 지켜야 할 규칙

1. 먼저 `AGENTS.md`, 이 파일, `docs/DOCUMENTATION_GUIDE.md`, `docs/GIT_CONVENTION.md`를 읽습니다.
2. 병렬 작업이면 `docs/workstreams/README.md`와 담당 트랙 문서를 읽습니다.
3. 사용자의 짧은 트랙 지시는 긴 역할 프롬프트로 자동 확장합니다. 작업 트랙, 수정 대상, 기록 위치, 주요 위험을 먼저 선언합니다.
4. 범위 없는 `뭐 해야 해?` 요청에는 트랙 설명과 다음 작업 후보를 먼저 보여주고, 사용자가 트랙을 고르게 돕습니다.
5. 한 PR에는 한 기능, 한 버그 수정, 한 문서 정리, 또는 한 CI/runtime 설정 변경만 담습니다.
6. 제목과 GitHub 라벨로 작업 트랙, 작업 타입, 크기를 구분합니다. 변경 파트는 필요할 때만 보조 라벨로 표시합니다.
7. dashboard, OCR, 모의투자, 인증, 보안, 운영 배포는 현재 MVP 작업에 섞지 않습니다.
8. PR 전에는 관련 테스트와 `git diff --check`를 실행합니다.
9. PR 본문에는 검증 결과를 자연어로 요약하고, 명령어는 보조 정보로 둡니다.
10. PR 제목은 명사형으로 끝내고, PR 본문과 Notion 작업 카드는 사람이 읽기 쉬운 카드형 구조로 씁니다.
11. PR 생성/수정 후 `gh pr view --json body --jq .body`와 `??` 검색으로 한글 깨짐이 없는지 확인합니다.
12. 제품 개발/운영 문제를 조사했거나 반복 가능성이 있으면 Notion 개발자 기술 경험 DB에 상세 기록을 남깁니다. Codex/Notion/PR/문서 운영 사고는 에이전트 운영 로그 DB에 남깁니다.
13. CI가 통과하면 squash merge하고 브랜치를 삭제합니다.

## 가장 가까운 다음 작업 후보

- 네이버 종토방 실제 HTML 변화에 맞춘 parser 보강
- 에펨코리아 게시판 parser 보강
- 종목 게시판형 소스를 위한 `CrawlTarget` 최소 설계
- 소스별 활성화 상태 설계
- pipeline이 backend readiness를 기다리도록 개선
- admin API Swagger 예시와 validation 오류 응답 정리
