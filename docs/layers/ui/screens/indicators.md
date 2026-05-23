# 주요 지표 화면

## Route

- Parent: root
- Overview route: `/indicators`
- Detail routes:
  - `/indicators/domestic`
  - `/indicators/us`
  - `/indicators/bonds`
  - `/indicators/commodities`

## 화면 목적

시장 전체 분위기를 일반 금융 대시보드처럼 길게 설명하지 않고, 핵심 지표와 커뮤니티 반응의 괴리를 한눈에 보여줍니다. 상세한 지표 묶음은 국내주식, 미국주식, 채권, 원자재 상세 route에서 확인합니다.

## 현재 섹션

- 핵심 지표 카드: 국내주식, 미국주식, 채권, 원자재
- 각 카드: 대표 변화율, 한 줄 해석, 지표 chip, 상세 route 링크
- 국장 섹터 방향: 정사각형에 가까운 섹터 타일, 상승/하락 방향, 강도 막대
- 미장 섹터 방향: AI 반도체, 빅테크, 에너지, 소비재, 헬스케어, 리츠
- 가격과 반응이 엇갈린 종목: 가격 변화, 반응 변화, 이유를 표로 표시
- 섹터·테마별 반응 히트맵: chip map
- 지표별 데이터 신선도
- 주요 일정: CPI, FOMC, 실적, 공시

## 상세 route 섹션

- 별도 분석 hero: 카테고리명, 대표 변화율, 전체 핵심 보기 링크
- 상세 KPI grid: 상승 섹터 수, 커뮤니티 괴리, 일정 민감도, 시장 폭
- 가격·반응 동시 변화 chart shell
- 지표별 데이터 신선도와 연결 키워드
- 가격과 반응이 엇갈린 종목 table

## UI 기준

- 탭 첫 화면은 핵심 정보만 보여줍니다.
- 긴 설명은 카드, chip, 막대, 표, 섹터 타일로 치환합니다.
- 상세 내용은 overview 카드 아래에 붙이지 않고 별도 route의 분석 페이지로 분리합니다.
- 상승은 빨강, 하락은 파랑 계열을 유지합니다.
- `추천`, `진입`, `확정 시그널` 같은 투자 자문형 표현은 쓰지 않습니다.

## API 후보

| Field | Owner Track | Description |
| --- | --- | --- |
| `marketGroups` | market/data | 국내주식, 미국주식, 채권, 원자재 핵심 지표 묶음 |
| `detailRows` | market/data | 상세 route별 지표 목록 |
| `domesticSectors` | market/data | 국장 섹터 방향과 강도 |
| `usSectors` | market/data | 미장 섹터 방향과 강도 |
| `anomalyRows` | market/data | 가격과 반응이 엇갈린 종목 |
| `freshnessRows` | backend | 지표별 데이터 신선도 |
| `schedules` | market/backend | 주요 일정 |

## 기획 확인 필요

- 상세 route의 최종 정보량과 API 응답 단위.
- 섹터 분류 기준: KRX 업종, 자체 테마, 외부 provider 분류 중 무엇을 우선할지.
- 채권/원자재 지표의 공개 배포 가능 데이터 provider.
