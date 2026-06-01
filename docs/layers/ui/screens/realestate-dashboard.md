# 부동산 대시보드

## Route

- Parent: root app
- Route 후보: `/dashboard`, `/realestate`
- Child screens: `realestate-target-detail`

## 화면 목적

사용자가 지금 어느 지역과 단지가 많이 언급되는지, 그 반응이 기대인지 우려인지, 어떤 쟁점과 시장 사실이 함께 움직이는지 빠르게 확인합니다.

## 현재 섹션

- 상단 검색: 지역, 단지, 법정동, 키워드 검색
- 요즘 언급 많은 지역/단지 ranking
- 기대/우려 split meter와 쟁점 비율
- 실시간 이슈, 뉴스, 컬럼 링크
- 실거래/전세/매물/정책 데이터 상태 badge
- 표본 신뢰도, source skew, 수집 지연 rail
- 에이전트 근거 로그 최신 항목

## 상태와 빈 화면

- loading: ranking skeleton, timeline skeleton, stale badge placeholder
- empty: 수집된 지역/단지 mention 없음, source 상태와 mock 여부 표시
- error: 수집/API 실패 영역별 표시
- stale/mock: provider, `asOf`, `stale`, `mock` badge를 카드마다 표시

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `targets[]` | realestate/indicator | 언급 많은 지역/단지 목록 |
| `targets[].reactionSnapshot` | indicator | 기대/우려/중립, mention count, confidence |
| `targets[].issueMix` | indicator | 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책 비율 |
| `targets[].marketFacts` | realestate | 실거래/전세/매물/정책 fact와 provider/asOf/stale |
| `issueFeed[]` | community/realestate | 뉴스/컬럼/커뮤니티 링크 |
| `evidenceLogs[]` | agent | 최신 평가와 근거 요약 |

## 기획자 확인 필요

- 첫 화면 route를 `/dashboard`로 유지할지 `/realestate`로 둘지
- target 식별자를 region과 complex로 분리 노출할지 통합 target으로 노출할지
- 반응 지표를 점수형으로 보여줄지 split meter 중심으로 보여줄지

## 변경 로그

- 2026-06-01: 부동산 전용 대시보드 Screen Brief 생성
