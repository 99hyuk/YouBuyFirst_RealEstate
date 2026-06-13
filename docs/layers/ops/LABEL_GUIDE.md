# 라벨/태그 사전

이 문서는 GitHub PR 라벨과 Notion 태그가 무엇을 뜻하는지 한눈에 보기 위한 기준표입니다. 새 작업자는 PR을 만들거나 Notion 작업 카드를 쓸 때 이 문서를 먼저 확인합니다.

## 빠른 구분

| 질문 | 볼 태그 |
| --- | --- |
| 어느 작업 영역인가? | `track:<작업영역>` |
| 어떤 종류의 변경인가? | 작업 타입 `type:*` |
| 어느 부분을 건드렸나? | 변경 파트 `part:*` |
| 리뷰 크기가 어느 정도인가? | `size:*` |
| Notion에서 지금 상태는? | `상태` |
| Notion에서 다음 우선순위는? | `우선순위` |

## GitHub PR 라벨

### 작업 타입 Type

| 라벨 | 의미 | 예시 |
| --- | --- | --- |
| `type:feat` | 사용자나 시스템의 새 동작 추가 | 신규 API, 새 화면, 새 배치 |
| `type:fix` | 버그 수정 | 파싱 오류, 잘못된 집계, 실패한 테스트 |
| `type:docs` | 문서만 변경 | 기획서, README, 작업 문서 |
| `type:refactor` | 동작 변경 없는 구조 개선 | 패키지 분리, 이름 정리 |
| `type:perf` | 성능 개선 | bulk insert, cache, query 최적화 |
| `type:chore` | 기타 유지보수 | 사소한 정리, 설정 보정 |

### 작업 영역 Track

작업 판단의 1차 기준은 `realestate`, `community`, `indicator`, `agent`, `ui`, `ops` 작업 영역입니다. GitHub 라벨 family는 기존 형식인 `track:*`를 유지하고, `track:` 뒤 값만 작업 영역 이름으로 씁니다.

| 라벨 | 작업 영역 | 담당 |
| --- | --- | --- |
| `track:realestate` | `realestate` | 지역/단지, alias, market fact, 정책/개발/교통 이벤트 |
| `track:community` | `community` | 커뮤니티 글 수집, 소스 어댑터, source policy, 원문 제한 저장 |
| `track:indicator` | `indicator` | 반응 방향, 쟁점 비율, 반응 지표, snapshot |
| `track:agent` | `agent` | 지역/단지 평가, 유사 과거 비교 설명, 근거 로그 |
| `track:ui` | `ui` | 사용자 화면, 디자인 시스템, mock data, API 연동 |
| `track:ops` | `ops` | 기획 조율, 문서, Notion, PR/CI, 배포 정책 |

과거 `track:crawl`, `track:data`, `track:front`는 닫힌 PR이나 기존 Notion 카드 해석용입니다. 새 PR은 `track:realestate`, `track:community`, `track:indicator`, `track:agent`, `track:ui`, `track:ops` 중 하나를 우선 사용합니다.

### 변경 파트 Part

`part:*`는 실제로 건드린 부분입니다. 리뷰 경로를 돕는 보조 라벨이라, 애매하면 생략해도 됩니다.

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
| `트랙` | 기존 속성명 유지. 값은 `realestate`, `community`, `indicator`, `agent`, `ui`, `ops` 중 하나 |
| `변경 파트` | 영향을 받은 코드/문서/규칙/자산 |
| `크기` | PR 리뷰 크기 |
| `검증` | 사람이 읽기 쉬운 검증 결과 |
| `다음 메모` | 다음 작업자가 바로 참고할 메모 |

### 다음 작업 DB

| 속성 | 의미 |
| --- | --- |
| `상태` | `Next`, `Ready`, `Later`, `Blocked` 중 하나 |
| `우선순위` | `P0` 긴급, `P1` 가까운 작업, `P2` 후속, `P3` 언젠가 |
| `트랙` | 기존 속성명 유지. 담당 작업 영역 값 |
| `변경 파트` | 영향을 받을 코드/문서/규칙/자산 |
| `예상 PR 크기` | 예상되는 리뷰 크기 |
| `완료 기준` | 이 작업이 끝났다고 말할 수 있는 조건 |

## 작성 원칙

- PR 제목은 `[작업영역][타입] 한국어 명사형 요약`으로 씁니다. 예: `[realestate][docs] 데이터 계약 기준 정리`
- PR 본문은 카드형 구조로 작성합니다.
- Notion 작업 카드는 PR 본문과 같은 흐름을 따릅니다.
- 명령어는 PR 본문 첫 화면에 길게 늘어놓지 않고 접힌 영역에 둡니다.
