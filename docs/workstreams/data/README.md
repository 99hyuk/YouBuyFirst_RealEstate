# data

## 역할

수집된 글을 투자 참고에 쓸 수 있는 분석 데이터로 바꿉니다. 이 트랙은 종목 인식, 반응 방향 분류, 열기 지수, 30분 집계를 맡고, 매수/매도 판단 자체는 `agent` 트랙에 넘깁니다.

## 담당 범위

- 종목명, 티커, 별칭 matcher
- 국내/미국 stock master 확장
- LLM provider interface와 analysis schema
- `bullish`, `bearish`, `neutral` 반응 방향 분류 품질
- 열기 지수 산식
- 30분 indicator snapshot
- AI 3줄 요약 입력 데이터
- 커뮤니티별 신호와 이후 수익률 비교용 원천 지표
- `CommunitySignal`, `ForwardReturn`, `CommunityPerformanceSnapshot`
- 종목 상세 팩트폭격 헤드라인의 기술/재무/밸류에이션 근거와 `stockHealthScore` 후보

## 파일 소유권

주로 담당:

- `pipeline/src/youbuyfirst_pipeline/matcher.py`
- `pipeline/src/youbuyfirst_pipeline/llm.py`
- `stock`, `analysis`, `indicator` 관련 backend domain
- indicator API
- stock seed/fixture

공유 전 협의:

- crawler raw payload
- quote provider contract
- dashboard API contract
- stock detail roast headline API contract
- agent decision input contract
- simulation order/portfolio schema

## 현재 우선순위

1. 종목 별칭 매칭 테스트 확장
2. 30분 집계 산식 검증 테스트 추가
3. 열기 지수 산식 문서화
4. 커뮤니티별 성과 비교용 snapshot 모델 설계
5. 종목 상세 팩트폭격 헤드라인에 넣을 기술/재무/밸류에이션 evidence schema 후보 정리

## 하지 않는 일

- 크롤러 우회 전략
- 시세 provider 직접 연동
- 모의 주문 체결
- AI 매매 판단과 페르소나 실행
- UI 레이아웃 구현
