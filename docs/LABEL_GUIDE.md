# 라벨/태그 사전

이 문서는 GitHub PR 라벨과 Notion 태그가 무엇을 뜻하는지 한눈에 보기 위한 기준표입니다. 새 작업자는 PR을 만들거나 Notion 작업 카드를 쓸 때 이 문서를 먼저 확인합니다.

## 빠른 구분

| 질문 | 볼 태그 |
| --- | --- |
| 어느 병렬 트랙인가? | `track:*` |
| 어떤 종류의 작업인가? | `type:*` |
| 어느 코드/문서 영역인가? | `area:*` |
| 리뷰 크기가 어느 정도인가? | `size:*` |
| Notion에서 지금 상태는? | `상태` |
| Notion에서 다음 우선순위는? | `우선순위` |

## GitHub PR 라벨

### Type

| 라벨 | 의미 | 예시 |
| --- | --- | --- |
| `type:feat` | 사용자나 시스템의 새 동작 추가 | 신규 API, 새 화면, 새 배치 |
| `type:fix` | 버그 수정 | 파싱 오류, 잘못된 집계, 실패한 테스트 |
| `type:docs` | 문서만 변경 | 기획서, README, 작업 문서 |
| `type:test` | 테스트 추가 또는 테스트 구조 변경 | fixture, unit test, smoke test |
| `type:refactor` | 동작 변경 없는 구조 개선 | 패키지 분리, 이름 정리 |
| `type:infra` | CI, Docker, 배포, 개발 환경 | workflow, compose, env |
| `type:data` | seed, fixture, 종목 마스터 데이터 | 종목 CSV, 테스트 HTML |
| `type:chore` | 기타 유지보수 | 사소한 정리, 설정 보정 |

### Track

`track:*`는 병렬 작업의 책임 경계입니다. 새 채팅에서 가장 먼저 고르는 라벨입니다.

| 라벨 | 트랙 | 담당 |
| --- | --- | --- |
| `track:data` | `community-data-platform` | 커뮤니티 수집, 소스 어댑터, 수집 타깃 |
| `track:signal` | `signal-intelligence` | 종목 인식, 감성 분석, 열기 지수 |
| `track:market` | `market-simulation-engine` | 시세, 모의투자, 에이전트 런타임 |
| `track:frontend` | `frontend-experience` | 사용자 대시보드, UI, mock data, API 연동 |
| `track:product` | `product-planning-ops` | 기획 조율, 문서, Notion, PR/CI, 배포 정책 |

### Area

`area:*`는 실제로 건드린 코드나 문서 표면입니다. 리뷰 경로를 돕는 보조 라벨이라, 애매하면 생략해도 됩니다.

| 라벨 | 의미 |
| --- | --- |
| `area:backend` | Spring Boot, DB schema, API, JPA |
| `area:worker` | Python crawler, matcher, LLM provider |
| `area:frontend` | 사용자 화면, 대시보드, UI 상태, mock 화면 |
| `area:ci` | GitHub Actions와 검증 환경 |
| `area:docs` | README, 기획, 작업 문서 |
| `area:process` | 작업 방식, 컨벤션, 인수인계 |
| `area:data` | 종목 마스터, fixture, seed |
| `area:runtime` | Docker Compose와 런타임 설정 |

### Size

| 라벨 | 기준 | 운영 원칙 |
| --- | --- | --- |
| `size:XS` | 1-2개 파일 | 매우 작은 수정 |
| `size:S` | 3-5개 파일 | 선호하는 PR 크기 |
| `size:M` | 6-10개 파일 | 리뷰 가능한 단일 작업 |
| `size:L` | 11개 이상 파일 | 분리 가능성을 먼저 검토하고 이유를 적음 |

## Notion 태그

### 작업 로그 DB

| 속성 | 의미 |
| --- | --- |
| `상태` | `Merged`, `Open`, `Draft`, `Blocked` 중 하나 |
| `트랙` | 다섯 병렬 트랙 중 하나 |
| `영역` | 영향을 받은 코드/문서 영역 |
| `크기` | PR 리뷰 크기 |
| `검증` | 사람이 읽기 쉬운 검증 결과 |
| `다음 메모` | 다음 작업자가 바로 참고할 메모 |

### 다음 작업 DB

| 속성 | 의미 |
| --- | --- |
| `상태` | `Next`, `Ready`, `Later`, `Blocked` 중 하나 |
| `우선순위` | `P0` 긴급, `P1` 가까운 작업, `P2` 후속, `P3` 언젠가 |
| `트랙` | 담당 병렬 트랙 |
| `영역` | 영향을 받을 코드/문서 영역 |
| `예상 PR 크기` | 예상되는 리뷰 크기 |
| `완료 기준` | 이 작업이 끝났다고 말할 수 있는 조건 |

## 트랙 아이콘

| 아이콘 | 트랙 | 표시 위치 |
| --- | --- | --- |
| 🕸️ | `community-data-platform` | 수집/크롤링 작업 |
| 📈 | `signal-intelligence` | 감성/지표 작업 |
| 💹 | `market-simulation-engine` | 시세/모의투자/에이전트 작업 |
| 🖥️ | `frontend-experience` | 화면/UI 작업 |
| 🧭 | `product-planning-ops` | 기획/운영/조율 작업 |

## 작성 원칙

- PR 제목은 `[트랙][타입] 명사형 요약`으로 씁니다. 예: `[product][docs] 프론트 트랙과 통합 브랜치 전략 분리`
- PR 본문은 카드형 구조로 작성합니다.
- Notion 작업 카드는 PR 본문과 같은 흐름을 따릅니다.
- 명령어는 PR 본문 첫 화면에 길게 늘어놓지 않고 접힌 영역에 둡니다.
