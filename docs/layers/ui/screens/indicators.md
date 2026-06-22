# 주요 일정 화면

## Route

- Parent: root
- Overview route: `/indicators`
- Legacy detail routes:
  - `/indicators/price-transaction`
  - `/indicators/supply-demand`
  - `/indicators/demand-mood`
  - `/indicators/macro-finance`

상단 내비게이션 노출명은 `주요 일정`입니다. 기존 지표 상세 route는 외부 링크나 과거 북마크가 깨지지 않도록 같은 일정 화면을 렌더링합니다.

## 화면 목적

기존의 가격·거래량/공급·수급/심리/금융 지표 허브는 폐기합니다. 이 화면은 부동산 시장을 볼 때 반복적으로 확인해야 하는 공식 발표, 통계 공개, 정책·금리·청약 일정을 캘린더 형태로 보여줍니다. 사용자는 일정을 눌러 공식 출처로 이동하고, 어떤 데이터를 언제 확인해야 하는지 빠르게 판단합니다.

## 현재 섹션

- 일정 히어로: 지역 분석/마이페이지 화면의 공통 헤더 타이포와 간격을 따르는 화면 제목, 공식 통계 바로가기, 페이지 용도 설명
- 월간 캘린더: 오른쪽 upcoming 패널 없이 화면 폭을 넓게 사용하며, 가격지수, 실거래, 미분양·공급, 금리, 청약, 정책 일정을 날짜별 chip으로 표시
- 공식 출처: 화면 하단의 보조 링크 줄로만 제공하며, 설명문 없이 출처명과 분류만 표시

## 일정 항목 기준

- 일정은 투자 행동을 지시하지 않고 `확인`, `점검`, `공개`, `발표`처럼 관찰형 동사로 표현합니다.
- 정확한 공표일이 provider별로 달라질 수 있으므로, 화면의 정적 일정은 `확정 발표일`이 아니라 `월간 점검 일정`으로 다룹니다.
- 실제 API가 붙으면 각 일정은 `provider`, `asOf`, `sourceUrl`, `scheduleDate`, `stale`, `lastCheckedAt`를 함께 가져야 합니다.

## 공식 출처

- 한국부동산원 R-ONE: 가격지수, 주간·월간 통계
- 국토교통부 실거래가 공개시스템: 매매·전월세 실거래
- 국토교통 통계누리: 미분양, 인허가, 착공, 준공 등 공급 통계
- 한국은행: 기준금리, 통화정책방향 결정회의
- 청약Home: 청약 접수, 당첨자 발표, 경쟁률
- 국토교통부: 정책, 공급, 교통, 정비사업 보도자료

## 상태와 빈 화면

- loading: 캘린더 frame과 skeleton 일정 chip을 먼저 보여줍니다.
- empty: 해당 월 일정이 없으면 공식 출처 링크를 유지하고 `일정 수집 전/insufficient`를 표시합니다.
- stale: 일정은 노출하되 마지막 확인 시각과 provider를 함께 표시합니다.
- error: 캘린더는 유지하고 출처별 오류를 분리합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `scheduleEvents` | content/realestate | 캘린더에 표시할 공식 일정 |
| `sourceLinks` | content/realestate | 공식 출처 링크 |
| `lastCheckedAt` | backend | provider별 마지막 확인 시각 |
| `stale` | backend | 일정 갱신 지연 여부 |

예상 endpoint:

- `GET /api/realestate/market-data-schedules?month=YYYY-MM`
- `GET /api/realestate/market-data-sources`

기존 `/api/realestate/indicators`, `/api/realestate/indicators/:category`, `/api/realestate/indicators/anomalies`는 이 화면의 필수 입력이 아닙니다. 지표 값 자체는 대시보드 오른쪽 지표 탭이나 대상 상세 화면에서 다룹니다.

## 기획 확인 필요

- 일정 데이터를 DB에 저장할 때 반복 일정 규칙을 둘지, 월별 materialized schedule로 둘지 결정해야 합니다.
- 공식 공표일이 지연될 때 `예정`, `지연`, `확인 완료` 상태를 어떤 badge로 표현할지 정해야 합니다.
- 정책·보도자료는 전체를 가져오면 노이즈가 커서, 부동산/공급/교통/대출 키워드 필터 기준이 필요합니다.

## 변경 로그

- 2026-06-22: 오른쪽 `이번 달 체크할 일정` 패널을 제거하고 월간 캘린더를 단일 컬럼 중심 화면으로 확대.
- 2026-06-22: 공식 출처 링크 영역을 설명문 없는 낮은 보조 링크 줄로 축소.
- 2026-06-22: 일정 히어로의 제목 굵기, 크기, 설명 텍스트를 지역 분석/마이페이지 공통 헤더 스타일과 통일.
- 2026-06-22: 기존 주요 지표 허브와 카테고리 상세 화면을 폐기하고, `/indicators`를 공식 일정 캘린더와 출처 링크 화면으로 전환.
