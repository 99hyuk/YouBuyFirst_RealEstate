# 종목 상세 화면

## Route

- Parent: `stocks`
- Route 후보: `/stocks/:symbol`
- Child screens:
  - `stock-news-detail`: 뉴스/공시/리포트 링크에서 들어가는 상세 또는 drawer
  - `stock-filing-detail`: 공시 상세
  - `stock-community-post`: 커뮤니티 글 snippet/출처 상세
  - `stock-indicator-detail`: 기술/재무 지표 개별 설명 panel

## 화면 목적

사용자가 한 종목의 현재 상태를 가격, 시황, 기술 지표, 재무, 뉴스/공시, 커뮤니티 반응, 컨센서스 근거로 빠르게 판단합니다. 이 화면은 투자 행동을 지시하지 않고, 관찰 가능한 상태와 근거를 압축해서 보여줍니다.

## 현재 섹션

- 종목 메타: 이름, 티커, 시장, 기준 시각, stale/mock 상태
- 팩트폭격 헤드라인 배너: 검은 상단 배너, `headlineTone`, `headline`, `subtitle`
- 핵심 요약 카드: 점수, 위험/강점, 주요 변동
- 가격 차트: 가격, 이동평균, 거래량
- CAN SLIM/분석 카드: 종목 상태를 점수와 근거로 분해
- 기술 지표: RSI, ADX, ATR, VWAP, RS 등급 등
- 재무 지표: PER, PBR, ROE, EPS 성장, 부채비율 등
- 뉴스/공시/애널리스트 근거: 외부 링크와 관련 키워드
- 커뮤니티 반응: 별도 섹션에서 원문/출처/반응 방향을 표시

## 상태와 빈 화면

- loading: 종목 메타와 skeleton chart를 먼저 보여줍니다.
- empty: 아직 분석 가능한 지표가 부족하다고 표시하고, 팩트폭격 배너는 `normal` 톤으로 낮춥니다.
- error: 가격/지표/뉴스 중 실패한 묶음을 분리해 표시합니다.
- stale/mock: `asOf`, `dataQuality`, mock 여부를 배너 또는 근거 영역에 노출합니다.

## API 후보

| 필드 | 소유 트랙 | 설명 |
| --- | --- | --- |
| `symbol` | backend/data | 종목 식별자 |
| `asOf` | backend/market/data | 분석 기준 시각 |
| `headlineTone` | agent/backend | `normal`, `spicy`, `roast` |
| `headline` | agent/backend | 상단 한줄평 |
| `subtitle` | agent/backend | 근거 지표 3-5개 요약 |
| `evidence` | market/data/agent | 헤드라인 근거 배열 |
| `dataQuality` | backend | `complete`, `stale`, `partial`, `mock`, `insufficient` |
| `personalizedSafe` | agent/front | 보유 종목 개인화 화면에 그대로 노출 가능한지 |
| `priceSeries` | market | 차트 데이터 |
| `technicalIndicators` | market/data | 기술 지표 |
| `fundamentalIndicators` | data | 재무/밸류에이션 지표 |
| `events` | backend/data | 뉴스, 공시, 가격 변화, 커뮤니티 이벤트 |
| `communityReaction` | data | 커뮤니티 반응 요약 |

## 기획자 확인 필요

- `roast` 톤을 공개 종목 상세의 기본 옵션으로 둘지, 데모/실험 플래그 뒤에 둘지.
- 보유 종목/관심종목 개인화 화면에서는 어느 수준까지 순화할지.
- 뉴스/공시/커뮤니티 글 상세를 별도 route로 둘지, drawer/panel로 둘지.
- CAN SLIM 분석을 실제 산식으로 구현할지, 종목 상태 점수의 보조 설명으로만 둘지.
- 팩트폭격 헤드라인을 backend가 생성할지, agent가 생성하고 backend가 캐시할지.

## 변경 로그

- 2026-05-18: 종목 상세 팩트폭격 헤드라인을 커뮤니티 요약이 아니라 시황/기술/재무 기반 종목 상태 카피로 분리.
- 2026-05-18: 하위 상세 화면 후보를 route/drawer 후보로 분리.
