# Crawl 소스 정책과 실행 단계 설계

## 배경

현재 pipeline은 `build_pipeline()`에서 adapter를 만들고, `CommunityPipeline.run_once()`가 각 adapter의 `fetch_posts()`를 바로 호출합니다. 즉 코드에 adapter가 등록되어 있으면 네이버 종토방이나 에펨코리아 수집이 실행될 수 있습니다.

이 설계는 크롤러가 외부 사이트를 보고 법적/운영 가능성을 자동 판단하게 만들자는 뜻이 아닙니다. 사람이 정한 내부 소스 정책을 pipeline 실행 단계가 지키게 만드는 것이 목적입니다.

소스 상태값 자체는 `2026-05-15-source-activation-state-design.md`의 `enabled`, `public-demo-only`, `local-research-only`, `disabled` 계약을 따릅니다. 이 문서는 그 상태값이 실제 수집 실행 흐름에서 어디에 들어가는지, 그리고 나중에 관리자 페이지 개념으로 어떻게 확장되는지를 정리합니다.

## 목표

- 사용자가 수집 실행 단계를 읽고 이해할 수 있게 합니다.
- adapter 호출 직전에 source policy gate를 두는 구조를 설계합니다.
- 로컬 연구 환경과 공개 실행 환경의 허용 조건을 분리합니다.
- 관리자 페이지에서 소스 상태를 관리하는 최종 개념까지 포함하되, 이번 구현 범위는 작게 유지합니다.

## 비목표

- 이번 설계에서 네이버/에펨코리아 parser를 보강하지 않습니다.
- 이번 설계에서 DB migration이나 관리자 화면을 바로 구현하지 않습니다.
- 이번 설계에서 특정 커뮤니티의 공개 운영 가능 여부를 확정하지 않습니다.
- 이번 설계에서 CAPTCHA 우회, 로그인 세션 수집, proxy rotation, fingerprint 위장을 다루지 않습니다.

## 현재 실행 단계

현재 흐름은 아래처럼 단순합니다.

```text
환경 변수 읽기
-> fetcher 생성
-> instrument CSV 로드
-> NAVER_STOCK_CODES 또는 KR 종목 기반으로 NaverBoardAdapter 생성
-> FmkoreaAdapter 생성
-> CommunityPipeline 생성
-> run-once 또는 scheduler 실행
-> 각 adapter.fetch_posts() 호출
-> parser가 RawPost 생성
-> matcher/LLM enrichment
-> backend ingestion
```

문제는 `adapter.fetch_posts()`가 외부 요청의 시작점인데, 그 직전에 "이 소스를 지금 실행해도 되는가"를 확인하는 단계가 없다는 점입니다.

## 목표 실행 단계

목표 흐름은 `adapter.fetch_posts()` 앞에 source policy gate를 추가합니다.

```text
환경 변수 읽기
-> 실행 환경 결정: local | public
-> source policy registry 로드
-> adapter 후보 생성
-> CommunityPipeline 생성
-> run-once 또는 scheduler 실행
-> source policy gate 확인
   -> 허용: adapter.fetch_posts() 호출
   -> 거부: 외부 요청 없이 skipped run 기록
-> 허용된 소스만 parser/enrichment/ingestion 진행
```

핵심은 adapter 내부가 아니라 pipeline 실행 경계에서 막는 것입니다. adapter는 "어떻게 가져오는가"를 맡고, policy gate는 "지금 가져와도 되는가"를 맡습니다.

## 상태별 실행 규칙

| 상태 | local 환경 | public 환경 | 외부 요청 |
| --- | --- | --- | --- |
| `enabled` | 실행 가능 | 실행 가능 | 허용 |
| `local-research-only` | 실행 가능 | skip | local에서만 허용 |
| `public-demo-only` | skip | skip | 금지, fixture/sample만 사용 |
| `disabled` | skip | skip | 금지 |

새 소스의 기본값은 `disabled`입니다. 현재 MVP 소스인 `NAVER`, `FMKOREA`는 공개 검토 전까지 `local-research-only`로 취급합니다.

## 내부 정책과 관리자 개념

이 설계의 최종 개념은 "관리자가 소스별 수집 상태를 정하고, 크롤러는 그 상태를 따른다"입니다.

단계는 세 개로 나눕니다.

1. Static policy 단계
   - pipeline 코드 또는 설정 파일에 소스 상태를 둡니다.
   - 예: `NAVER=local-research-only`, `FMKOREA=local-research-only`
   - 이번 crawl 구현 범위는 여기까지입니다.

2. Admin 조회 단계
   - backend admin API에서 현재 소스 상태를 조회할 수 있게 합니다.
   - 예: `GET /admin/crawl-sources`
   - 운영자가 "현재 어떤 소스가 왜 막혀 있는지"를 볼 수 있게 합니다.

3. Admin 변경 단계
   - 관리자 페이지 또는 admin API에서 소스 상태를 변경합니다.
   - 예: `NAVER`를 `disabled`로 내리거나, 공개 시연에서 `public-demo-only`로 둡니다.
   - 이 단계는 DB schema, audit log, 권한, front 화면이 엮이므로 별도 PR로 다룹니다.

이번 설계 문서에는 세 단계를 모두 설명하지만, 구현 PR은 1단계만 다룹니다.

## 권장 접근

세 가지 접근을 비교했습니다.

| 접근 | 설명 | 장점 | 단점 |
| --- | --- | --- | --- |
| Adapter 내부 분기 | 각 adapter의 `fetch_posts()` 안에서 상태를 확인 | adapter별 예외 처리 가능 | 정책이 흩어지고 새 adapter마다 반복 |
| Pipeline gate | `CommunityPipeline.run_once()`에서 adapter 호출 전 확인 | 외부 요청 시작점이 한곳에 모임 | pipeline이 source policy를 알아야 함 |
| Scheduler gate | scheduler가 허용된 adapter만 pipeline에 넘김 | 실행 전 필터링이 명확함 | `run-once`와 scheduler 경로가 갈라질 수 있음 |

추천은 Pipeline gate입니다. `run-once`와 `serve`가 모두 `CommunityPipeline.run_once()`를 거치기 때문에, 가장 적은 코드로 모든 실행 경로를 통제할 수 있습니다.

## 컴포넌트 설계

### SourcePolicy

소스의 상태와 설명을 담습니다.

```text
source: NAVER
status: local-research-only
reason: 공개 운영 검토 전 로컬 연구용 수집만 허용
```

초기에는 Python enum과 dataclass로 충분합니다.

### SourcePolicyRegistry

source 이름으로 policy를 찾습니다.

```text
get("NAVER") -> local-research-only
get("UNKNOWN") -> disabled
```

등록되지 않은 새 소스는 `disabled`로 처리합니다.

### CrawlRuntimeEnvironment

현재 pipeline 실행 환경을 나타냅니다.

```text
local
public
```

초기에는 환경 변수로 결정합니다. 예: `CRAWL_RUNTIME_ENV=local`. 값이 없거나 알 수 없는 값이면 `public`처럼 다루는 fail-closed 방식을 제안합니다. 로컬 개발자는 `.env` 또는 실행 명령에서 명시적으로 `CRAWL_RUNTIME_ENV=local`을 넣어야 수집이 열립니다. 공개 배포에서 환경 변수를 빼먹었을 때 외부 요청이 나가는 것보다, 로컬에서 한 번 더 설정해야 하는 불편이 더 안전합니다.

### SourcePolicyGate

`policy + runtime environment`를 받아 실행 여부를 반환합니다.

```text
allow(NAVER, local) -> true
allow(NAVER, public) -> false
allow(DISABLED_SOURCE, local) -> false
```

거부 결과에는 사람이 읽을 수 있는 이유를 포함합니다.

```text
source=FMKOREA
status=local-research-only
environment=public
reason=local research source is not allowed in public runtime
```

## Skip 기록 방식

정책 때문에 실행하지 않은 경우는 실패가 아니라 의도된 skip입니다. 외부 사이트 차단이나 HTTP 오류와 섞으면 안 됩니다.

초기 구현에서는 `run_once()` 결과에 아래 형태를 반환합니다.

```text
{
  "source": "NAVER",
  "status": "skipped",
  "skipReason": "source policy local-research-only is not allowed in public runtime"
}
```

backend `crawl_runs`에 기록할지는 구현 시점에 한 번 더 확인합니다. 기존 backend 상태값이 `SUCCESS`, `PARTIAL_FAILURE`, `FAILED` 중심이라면, 정책 skip을 억지로 failure로 넣지 않는 편이 낫습니다. 필요하면 후속 backend 계약 PR에서 `SKIPPED` 상태를 추가합니다.

## 운영 절차

소스 상태 변경은 단순 스위치가 아니라 운영 판단입니다. 아래 순서를 기본으로 둡니다.

1. 변경하려는 소스와 목표 상태를 정합니다.
2. 공개 배포, 원문 노출, 작성자 추적, robots/약관 리스크를 확인합니다.
3. 상태 변경 이유를 작업 로그나 운영 로그에 남깁니다.
4. static policy 단계에서는 PR로 상태를 바꿉니다.
5. admin 변경 단계가 생기면 audit log와 변경자를 기록합니다.
6. 변경 후 `run-once`나 fake adapter 테스트로 외부 요청 여부를 확인합니다.

예시:

```text
NAVER local-research-only -> disabled
이유: 접근 차단 또는 공개 배포 전 정책 재검토
결과: local/public 모두 외부 요청 없음
```

```text
FMKOREA local-research-only -> public-demo-only
이유: 공개 시연에서는 실제 수집 대신 샘플 데이터만 표시
결과: 외부 요청 없음, front는 sample/demo 상태 표시
```

## 구현 범위 제안

이번 crawl PR에서 다룰 범위:

- `pipeline/src/youbuyfirst_pipeline/source_policy.py` 추가
- `CommunityPipeline`에 source policy gate 주입
- `main.build_pipeline()`에서 static registry와 runtime environment 생성
- `disabled`, `public-demo-only`, public 환경의 `local-research-only`가 adapter를 호출하지 않는 테스트 추가
- skip 결과가 사람이 읽을 수 있는 reason을 포함하는지 테스트

이번 PR에서 다루지 않을 범위:

- backend `crawl_runs`에 `SKIPPED` 상태 추가
- admin API와 관리자 화면
- DB 기반 source policy 저장
- parser HTML 보강
- `CrawlTarget` queue 구현

## 검증 기준

- `UNKNOWN` source는 기본 `disabled`로 처리됩니다.
- public 환경에서 `NAVER`, `FMKOREA`가 `local-research-only`이면 `fetch_posts()`가 호출되지 않습니다.
- local 환경에서 `NAVER`, `FMKOREA`가 `local-research-only`이면 기존처럼 수집이 실행될 수 있습니다.
- `public-demo-only`와 `disabled`는 어떤 환경에서도 외부 요청을 보내지 않습니다.
- skip은 실패와 구분되는 결과로 반환됩니다.
- 기존 parser fixture test는 그대로 통과합니다.

## 남은 리스크

- 공개 배포 환경을 어떤 환경 변수로 판정할지 명확히 운영 문서에 적어야 합니다.
- backend에 `SKIPPED` 상태가 없으면 정책 skip의 장기 기록이 약할 수 있습니다.
- 관리자 페이지에서 상태 변경을 허용하려면 권한, audit log, rollback 정책이 필요합니다.
- `enabled`는 법적 안전을 뜻하지 않습니다. 검토가 끝난 운영 소스라는 내부 상태일 뿐이며, 공개 재게시나 작성자 추적 금지 원칙은 계속 유지됩니다.

## 다음 단계

사용자가 이 설계를 승인하면 `crawl` 구현 계획을 별도로 작성합니다. 계획은 static source policy registry와 pipeline gate 구현까지만 다루고, admin API와 화면은 후속 작업으로 분리합니다.
