# data AI mention resolver design

## 목표

단어 matcher는 종목 후보를 빠르게 찾는 역할로 유지하고, AI provider가 후보별 실제 종목 언급 여부와 반응 방향을 함께 판단하도록 pipeline 내부 계약을 정리한다.

이번 1차 PR은 pipeline 내부 계약과 테스트까지만 다룬다. backend 저장 schema, ingestion API, front 표시 계약, agent 입력 계약은 바꾸지 않는다.

## 책임 분리

- `InstrumentMatcher`: 제목과 본문에서 stock master 기반 후보 `Mention`을 만든다.
- `LLMProvider.resolve_mentions`: 후보별로 실제 종목 언급인지 판단하고, 실제 언급이면 반응 방향을 함께 반환한다.
- `CommunityPipeline._enrich`: accepted decision만 `mentions`와 `analyses`로 변환해 backend로 넘긴다.
- Backend: 기존 `mentions`와 `sentiments` payload를 그대로 받는다.

## 내부 모델

새 내부 모델 `MentionDecision`을 추가한다.

- `market`: 후보 종목 market
- `symbol`: 후보 종목 symbol
- `matched_text`: matcher가 찾은 원문 표현
- `is_mentioned`: AI가 실제 종목 언급으로 인정했는지 여부
- `reaction_direction`: `bullish`, `bearish`, `neutral` 중 하나. `is_mentioned`가 false이면 `neutral`로 둔다.
- `confidence`: 0부터 1 사이
- `rationale`: 짧은 판단 근거
- `model`: 판단 provider/model 이름

기존 `Analysis`는 backend payload 호환을 위해 유지한다. pipeline은 `is_mentioned == true`인 decision만 `Analysis`로 바꾼다.

## Provider 계약

`LLMProvider`는 `analyze` 대신 `resolve_mentions`를 제공한다. OpenAI provider는 JSON schema 응답을 `mentionDecisions` 배열로 받는다.

각 decision은 반드시 입력 후보 중 하나여야 한다. provider가 DB에 없는 종목을 새로 만들거나, 후보에 없는 symbol을 반환해도 pipeline은 accepted 결과로 쓰지 않는다.

## Mock 동작

mock provider는 실제 AI가 아니므로 보수적 휴리스틱만 둔다.

- `애플` 후보는 과일 맥락이면 `is_mentioned=false`
- `삼성전자` 후보가 `삼성 그룹` 맥락으로만 보이면 `is_mentioned=false`
- 나머지 후보는 기존 keyword 기반으로 `bullish`, `bearish`, `neutral`을 판단한다.

mock은 제품 판단 품질을 보장하지 않는다. 테스트와 로컬 demo가 같은 계약을 쓰게 하는 목적이다.

## 테스트 범위

- `MockLLMProvider.resolve_mentions`가 실제 언급과 비언급 후보를 구분한다.
- `_enrich`가 rejected 후보를 backend로 넘길 `mentions`와 `analyses`에서 제외한다.
- 기존 matcher 테스트와 crawler 테스트는 그대로 통과해야 한다.

## 제외 범위

- backend DB에 rejected decision을 별도 저장하지 않는다.
- OpenAI 실제 호출 통합 테스트는 추가하지 않는다.
- 새로운 종목 발견 기능을 만들지 않는다.
- 매수, 매도, 관망 판단은 agent 트랙으로 남긴다.
