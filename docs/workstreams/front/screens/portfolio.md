# 내 포트폴리오 화면

## Route

- Parent: root
- Route 후보: `/portfolio`
- Child screens: OCR 상세 확인 drawer 후보

## 화면 목적

가상 예수금, 보유 종목, 주문/원장, OCR 후보, 체결 후 복기를 한 화면에서 비교합니다. 실제 계좌 연동이 아니라 포트폴리오 mock과 향후 OCR 연동 설계를 보여줍니다.

## 현재 섹션

- 포트폴리오 제목과 `실거래 아님` badge
- 요약 KPI: 가상 예수금, 평가금액, 총 손익, 수익률, OCR 후보
- 보유 종목과 커뮤니티 반응 연결
- 자산 OCR · 주식 계좌 연결 준비 card
- OCR/거래내역 후보
- 주문 내역
- 원장 내역
- 체결 후 복기

## 상태와 빈 화면

- loading: KPI와 보유 종목 skeleton을 보여줍니다.
- empty: 가상 포트폴리오가 없으면 OCR/수기 입력 후보만 보여줍니다.
- error: OCR 파싱, 주문 내역, 원장 내역 실패를 분리합니다.
- stale/mock: 수수료 mock, 체결 mock, 가격 snapshot mock을 명확히 표시합니다.

## API 후보

| 필드 | 소유 트랙 | 설명 |
| --- | --- | --- |
| `summary` | trade | 가상 예수금, 평가금액, 총 손익, 기간별 수익률 |
| `holdings` | trade/market | 보유 종목, 수량, 평균단가, 현재가, 평가손익 |
| `orders` | trade/agent | 주문 요청, 체결, 취소, 실패, 스킵 |
| `ledger` | trade | 현금 변동, 체결 금액, 수수료 mock, 포지션 갱신 |
| `importPreview` | front/trade | OCR/CSV/수기 입력 후보와 confidence |
| `reviews` | trade/data/agent | 체결 후 커뮤니티 반응, 뉴스, 가격 변화 복기 |

## 기획자 확인 필요

- OCR은 실제 업로드 전 로컬 미저장 mock으로만 둘지.
- 계좌번호, 이름, 주문번호 같은 민감정보 제거 기준.
- 에이전트 판단과 내 포트폴리오 연결을 어느 화면에서 상세화할지.

## 변경 로그

- 2026-05-18: Screen Brief 신규 작성. OCR 후보와 모의 원장 기반 포트폴리오 구조를 정리.
