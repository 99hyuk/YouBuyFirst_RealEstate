# 지역/단지 상세 화면

## Route

- Parent: `/realestate/reactions`
- Route 정보: `/realestate/targets/:targetId`
- 연결 화면:
  - `/realestate/map`: 지도 기반 리포트
  - `/realestate/reactions?view=signals`: 반응 지표
  - `/indicators`: 주요 지표

> 새 구현과 문서는 `/realestate/targets/:targetId`를 기준으로 둡니다. 레거시 상세 route는 active route에서 제거했습니다.

## 화면 목적

사용자가 지역·단지 순위나 지도에서 특정 대상을 눌렀을 때, 가격 흐름, 전세·공급·수급 지표, 커뮤니티 반응, 핵심 쟁점, 근거 링크 후보를 한 화면에서 확인하게 합니다. 단정적 투자 판단이 아니라 관찰 근거와 위험 신호를 분리해 보여줍니다.

## 현재 섹션

- 상세 hero: 지역/단지명, 한줄 브리핑, 관찰 기간, 지표/반응 요약
- 핵심 KPI: 실거래가 흐름, 전세가율, 거래량, 미분양/공급 신호
- 커뮤니티 반응 추이: 언급량, 기대/우려/중립 비율, 급증 키워드
- 핵심 쟁점: 정책, 교통, 학군, 입주 물량, 전세 매물 등 원인 후보
- 신뢰도: 출처 수, stale 여부, alias match confidence
- 시간대별 변화: 최근 반응 변화와 이벤트 timeline
- 근거 링크 후보: 뉴스, 리포트, 커뮤니티, 공공데이터

## 상태와 빈 화면

- loading: 상세 hero와 KPI skeleton을 먼저 보여줍니다.
- empty: 해당 target id를 찾지 못하면 기본 지역과 순위 화면 링크를 제공합니다.
- error: 실거래, 커뮤니티, 뉴스, alias match 실패를 분리합니다.
- stale/mock: 신고 지연, 공개 지연, mock 데이터 여부를 KPI별로 표시합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `targetId` | realestate/backend | 내부 지역/단지 id |
| `targetName` | realestate/backend | 표시명 |
| `marketMeta` | realestate/backend | 시도, 시군구, 생활권, 단지군 |
| `priceSnapshot` | market/realestate | 실거래가, 가격지수, 기준일 |
| `leaseSnapshot` | market/realestate | 전세가율, 전세가격지수, 전세수급 |
| `supplySnapshot` | market/realestate | 미분양, 인허가, 착공, 준공 |
| `reactionSummary` | indicator/community | 언급량과 반응 방향 |
| `issueRows` | content/community | 핵심 쟁점과 원인 후보 |
| `evidenceLinks` | backend/content | 근거 링크 후보 |
| `quality` | backend | stale, confidence, source count |

## 기획 확인 필요

- 지역 단위와 단지 단위를 같은 화면에서 보여줄지, 단지 상세는 별도 route로 분리할지.
- 공공데이터가 없는 단지는 커뮤니티 반응만으로 얼마나 보여줄지.
- 리포트 panel과 상세 page의 정보량을 어디서 나눌지.

## 변경 로그

- 2026-06-01: 기존 상세 화면을 지역/단지 상세 리포트 화면으로 전환.
- 2026-06-12: 레거시 상세 route를 제거하고 상세 route param과 화면 문구를 부동산 대상 `targetId` 기준으로 정리.
