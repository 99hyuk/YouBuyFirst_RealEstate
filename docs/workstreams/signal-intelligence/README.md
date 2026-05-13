# signal-intelligence

## 역할

수집된 글을 종목 신호로 바꾸고, 그 신호가 실제 가격 변화와 어떤 관계가 있는지 검증합니다. 이 트랙은 너나사의 "인간지표" 자체를 만드는 영역입니다.

## 담당 범위

- 종목명, 티커, 별칭 matcher
- 국내/미국 instrument master 확장
- LLM provider interface와 sentiment schema
- `bullish`, `bearish`, `neutral` 분류 품질
- 열기 지수 산식
- 30분 metric snapshot
- AI 3줄 요약 입력 데이터
- 커뮤니티별 수익률 비교 에이전트
- `CommunitySignal`, `ForwardReturn`, `CommunityPerformanceSnapshot`

## 파일 소유권

주로 담당:

- `worker/src/youbuyfirst_worker/matcher.py`
- `worker/src/youbuyfirst_worker/llm.py`
- sentiment/metrics 관련 backend domain
- metrics API
- instrument seed/fixture

공유 전 협의:

- crawler raw payload
- quote provider contract
- dashboard API contract
- simulation order/portfolio schema

## 현재 우선순위

1. 종목 별칭 매칭 테스트 확장
2. 30분 집계 산식 검증 테스트 추가
3. 열기 지수 산식 문서화
4. 커뮤니티별 수익률 비교 에이전트의 최소 데이터 모델 설계

## 하지 않는 일

- 크롤러 우회 전략
- 시세 provider 직접 연동
- 모의 주문 체결
- UI 레이아웃 구현
