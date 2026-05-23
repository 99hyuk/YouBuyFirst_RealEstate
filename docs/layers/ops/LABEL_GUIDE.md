# 라벨/태그 사전

이 문서는 GitHub PR 라벨과 Notion 태그가 무엇을 뜻하는지 한눈에 보기 위한 기준표입니다. 새 작업자는 PR을 만들거나 Notion 작업 카드를 쓸 때 이 문서를 먼저 확인합니다.

## 빠른 구분

| 질문 | 볼 태그 |
| --- | --- |
| 어느 작업 영역인가? | 작업 영역 + legacy 라벨 `track:*` |
| 어떤 종류의 변경인가? | 작업 타입 `type:*` |
| 어느 부분을 건드렸나? | 변경 파트 `part:*` |
| 리뷰 크기가 어느 정도인가? | `size:*` |
| Notion에서 지금 상태는? | `상태` |
| Notion에서 다음 우선순위는? | `우선순위` |

## GitHub PR 라벨

### 작업 타입 Type

`type:*`는 이 PR이 어떤 종류의 변경인지 설명합니다. 기능 추가인지, 버그 수정인지, 문서 정리인지처럼 “무슨 일을 했는가”를 나타냅니다.

| 라벨 | 의미 | 예시 |
| --- | --- | --- |
| `type:feat` | 사용자나 시스템의 새 동작 추가 | 신규 API, 새 화면, 새 배치 |
| `type:fix` | 버그 수정 | 파싱 오류, 잘못된 집계, 실패한 테스트 |
| `type:docs` | 문서만 변경 | 기획서, README, 작업 문서 |
| `type:refactor` | 동작 변경 없는 구조 개선 | 패키지 분리, 이름 정리 |
| `type:perf` | 성능 개선 | bulk insert, cache, query 최적화 |
| `type:chore` | 기타 유지보수 | 사소한 정리, 설정 보정 |

### 작업 영역과 Legacy Track

작업 판단의 1차 기준은 `community`, `stock`, `indicator`, `market`, `simulation`, `agent`, `ui`, `ops` 작업 영역입니다. `track:*`는 GitHub와 Notion에 남아 있는 legacy 라벨입니다. 새 PR 본문에는 primary work area를 병기합니다.

| legacy 라벨 | primary work area | 담당 |
| --- | --- | --- |
| `track:crawl` | `community` | 커뮤니티 글 수집, 소스 어댑터, source policy, 원문 제한 저장 |
| `track:data` | `stock` 또는 `indicator` | 종목 인식, 별칭 매칭, 반응 방향, 열기 지수, 개미 심리 지수 |
| `track:market` | `market` | 실시간/지연 시세, 차트 캔들, quote cache, 수급 |
| `track:trade` | `simulation` | 가상 계좌, 주문, 체결, 원장, 포트폴리오, 수익률 |
| `track:agent` | `agent` | AI 판단, 커뮤니티별 성과 비교, 결정 로그, 헤드라인 |
| `track:front` | `ui` | 사용자 화면, 디자인 시스템, mock data, API 연동 |
| `track:ops` | `ops` | 기획 조율, 문서, Notion, PR/CI, 배포 정책 |

### 변경 파트 Part

`part:*`는 실제로 건드린 부분입니다. 리뷰 경로를 돕는 보조 라벨이라, 애매하면 생략해도 됩니다. 예를 들어 `track:ops` 작업이라도 PR 템플릿 파일을 바꾸면 `part:rule`이나 `part:docs`를 붙일 수 있습니다.

| 라벨 | 의미 |
| --- | --- |
| `part:backend` | Spring Boot, DB schema, API, JPA |
| `part:pipeline` | Python crawler/analysis pipeline, matcher, LLM provider |
| `part:front` | 사용자 화면, 대시보드, UI 상태, mock 화면 |
| `part:ci` | GitHub Actions와 검증 환경 |
| `part:runtime` | Docker Compose와 로컬 실행 설정 |
| `part:docs` | README, 기획, 작업 문서 |
| `part:rule` | 작업 규칙, 컨벤션, 인수인계, Notion 운영 기준 |
| `part:asset` | 코드가 참조하는 데이터 자산, seed, fixture, mock |

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
| `트랙` | legacy 속성명. 값은 기존 track alias를 쓰되 카드 본문에 primary work area를 병기 |
| `변경 파트` | 영향을 받은 코드/문서/규칙/자산 |
| `크기` | PR 리뷰 크기 |
| `검증` | 사람이 읽기 쉬운 검증 결과 |
| `다음 메모` | 다음 작업자가 바로 참고할 메모 |

### 다음 작업 DB

| 속성 | 의미 |
| --- | --- |
| `상태` | `Next`, `Ready`, `Later`, `Blocked` 중 하나 |
| `우선순위` | `P0` 긴급, `P1` 가까운 작업, `P2` 후속, `P3` 언젠가 |
| `트랙` | legacy 속성명. 담당 primary work area를 다음 메모나 본문에 병기 |
| `변경 파트` | 영향을 받을 코드/문서/규칙/자산 |
| `예상 PR 크기` | 예상되는 리뷰 크기 |
| `완료 기준` | 이 작업이 끝났다고 말할 수 있는 조건 |

## 작업 영역 아이콘

| 아이콘 | 작업 영역 | 표시 위치 |
| --- | --- | --- |
| 🕸️ | `community` | 수집/크롤링 작업 |
| 🧾 | `stock` | 종목 master/별칭/식별 작업 |
| 📊 | `indicator` | 반응 분석/집계/개미 심리 지수 작업 |
| 💹 | `market` | 시세/호가 작업 |
| 💰 | `simulation` | 모의투자/체결/원장 작업 |
| 🧠 | `agent` | 전략 에이전트 작업 |
| 🖥️ | `ui` | 화면/UI 작업 |
| 🧭 | `ops` | 기획/운영/조율 작업 |

## 작성 원칙

- PR 제목은 마이그레이션 전까지 `[legacy-alias][타입] 명사형 요약`으로 씁니다. 예: `[ops][docs] 작업 영역과 legacy 라벨 기준 정리`
- PR 본문은 카드형 구조로 작성합니다.
- Notion 작업 카드는 PR 본문과 같은 흐름을 따릅니다.
- 명령어는 PR 본문 첫 화면에 길게 늘어놓지 않고 접힌 영역에 둡니다.
