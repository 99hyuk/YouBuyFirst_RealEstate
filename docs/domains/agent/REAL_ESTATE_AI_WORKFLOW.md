# 부동산 AI 분석 워크플로우 결정

작성일: 2026-06-11

## 결론

MVP에서는 AI 분석을 Spring 요청 흐름 안에서 즉시 실행하지 않는다.

기본 구조는 `Python pipeline -> Spring Boot 저장/API -> Vue 화면 조회`로 둔다. Python pipeline은 크롤링, 별칭 매칭, 반응 분류, 쟁점 분류, AI 리포트/evidence log 생성을 맡고, Spring Boot는 작업 요청, DB 저장, 트랜잭션, 화면 조회 API를 맡는다.

LangGraph는 초기 필수 엔진으로 쓰지 않는다. 다만 지역/단지 상세 리포트처럼 분기, 재시도, guardrail, human review, evidence log 저장이 필요한 분석에는 `RealEstateEvaluationGraph` 파일럿으로 도입할 수 있다.

## 왜 이렇게 가는가

- 서비스는 실시간 챗봇이 아니라 수집된 반응과 시장 데이터를 분석해 보여주는 관찰형 서비스다.
- 화면 요청마다 AI를 호출하면 응답 속도, 비용, 실패 전파 문제가 커진다.
- 부동산 분석은 공개 데이터 지연, 표본 부족, 출처 편중, 별칭 ambiguity 때문에 사전 분석과 저장된 근거 로그가 중요하다.
- 현재 repo에는 이미 `pipeline/src/youbuyfirst_pipeline/llm.py`의 OpenAI structured output 흐름과 Spring Boot ingestion/API 구조가 있다.
- AI 출력은 화면 문구가 아니라 `evidence_logs`, `evidence_log_items`, `reaction_analyses`, `reaction_snapshots` 같은 구조화된 결과로 남겨야 한다.

## 역할 분리

| 영역 | 역할 | AI 호출 여부 |
| --- | --- | --- |
| Python pipeline | 수집, 별칭 매칭, 언급 판별, 반응/쟁점 분류, 리포트 생성 | 예 |
| Spring Boot | 분석 job 생성, DB 저장, 화면 조회 API, 관리자 검수 API | 기본적으로 아니오 |
| Vue front | 저장된 분석 결과 표시, stale/mock/asOf/provider 노출 | 아니오 |
| LangGraph | 복잡한 리포트 생성 workflow의 상태/분기/재시도 관리 | 선택 |
| Spring AI | 추후 Java 내부 간단 요약/관리자 기능 후보 | 보류 |

## AI가 담당할 기능

1. 지역/단지 언급 판별
   - 게시글과 후보 alias를 보고 실제 부동산 target 언급인지 판별한다.
   - 결과는 `real_estate_mentions`, `reaction_analyses`로 이어진다.

2. 반응 방향 분류
   - 기대, 우려, 중립, 정보성으로 분류한다.
   - 매수/매도/청약/대출 권유 문구로 변환하지 않는다.

3. 쟁점 분류
   - 전세, 공급, 교통, 학군, 재건축, 청약, 대출, 금리, 정책 같은 `issue_taxonomy` 기준으로 분류한다.

4. 지역/단지 리포트 생성
   - reaction snapshot, market fact, policy event, content item, source coverage를 읽어 요약한다.
   - 결과는 `evidence_logs`, `evidence_log_items`에 저장한다.

5. 문구 guardrail 검사
   - 금지 표현: 추천, 사라, 매수 기회, 청약 넣어라, 대출 받아라, 무조건 오른다, 수익 보장 등.
   - 금지 표현이 나오면 재생성하거나 `skipReason`을 남긴다.

## 기본 데이터 흐름

```text
공개 커뮤니티/뉴스/공공데이터 수집
  -> Python pipeline
  -> alias/target 후보 매칭
  -> AI 언급 판별 및 반응 분류
  -> reaction snapshot/issue mix 집계
  -> 시장 fact와 정책 event 결합
  -> evidence log 생성
  -> Spring API 또는 DB 저장
  -> Vue 화면 조회
```

## LangGraph 파일럿 후보

초기에는 함수 체인으로 충분하다.

```text
match_aliases()
resolve_mentions()
classify_reactions()
aggregate_snapshots()
generate_evidence_log()
validate_guardrails()
```

아래 조건이 생기면 LangGraph 파일럿을 시작한다.

- 분석 단계가 5단계 이상으로 늘어난다.
- confidence, stale, source skew에 따른 분기가 많아진다.
- 관리자 검수 대기 상태가 필요하다.
- 실패한 분석을 중간 단계부터 재시작해야 한다.
- 언급 판별, 쟁점 분류, 리포트 작성, 문구 검수 역할을 분리해야 한다.
- 실행 흐름 자체를 evidence/debug 로그로 남겨야 한다.

파일럿 이름은 `RealEstateEvaluationGraph`로 둔다.

```text
load_target_context
  -> load_reaction_snapshot
  -> load_market_facts
  -> load_policy_events
  -> evaluate_data_quality
  -> generate_evidence_summary
  -> validate_guardrails
  -> persist_evidence_log
```

분기 기준:

```text
confidence 낮음 -> human_review_required
market_fact stale -> add_caveat
source_skew 높음 -> lower_confidence
forbidden_copy_detected -> regenerate_summary
evidence 부족 -> skip_with_reason
```

## Spring API 후보

Spring은 AI를 직접 실행하기보다 작업과 결과를 관리한다.

```text
POST /api/realestate/analysis-jobs
GET  /api/realestate/analysis-jobs/{jobId}
GET  /api/realestate/targets/{targetId}/evidence-logs
GET  /api/realestate/targets/{targetId}/evaluation
POST /api/admin/realestate/mention-reviews/{mentionId}
```

## 저장해야 할 최소 결과

```json
{
  "targetId": "target-id",
  "windowStart": "2026-06-11T00:00:00+09:00",
  "windowEnd": "2026-06-11T01:00:00+09:00",
  "evaluationVersion": "realestate-eval-v1",
  "model": "gpt-4.1-mini",
  "tone": "watch",
  "summary": "전세 우려와 교통 기대가 동시에 관찰됩니다.",
  "evidence": [],
  "caveats": ["market_fact_stale"],
  "dataQuality": "partial",
  "confidence": 0.72,
  "skipReason": null,
  "asOf": "2026-06-11T01:03:00+09:00"
}
```

## 다음 작업

1. `realestate-eval-v1` 입력/출력 JSON schema를 확정한다.
2. 기존 `pipeline/src/youbuyfirst_pipeline/llm.py`의 stock mention prompt를 부동산 target mention prompt로 분리한다.
3. `MockRealEstateAIProvider`와 `OpenAIRealEstateAIProvider`를 만든다.
4. Spring에 analysis job 상태 모델을 추가할지, pipeline이 직접 ingestion API로 밀지 결정한다.
5. `evidence_logs`, `evidence_log_items` 저장 API 또는 JPA 모델을 우선 구현한다.
6. forbidden copy guardrail 테스트를 만든다.
7. LangGraph는 위 함수 체인이 복잡해진 뒤 `RealEstateEvaluationGraph`로 전환한다.

## 보류 사항

- Spring AI 도입은 보류한다. Java 내부에서 간단한 관리자 요약이나 on-demand preview가 필요해질 때 재검토한다.
- LangGraph 도입은 보류한다. evidence log 생성 workflow가 분기/재시도/검수 상태를 실제로 요구할 때 파일럿으로 시작한다.
- 화면 요청 중 즉시 AI 호출은 하지 않는다. 예외가 필요하면 별도 cache/asOf/stale 정책을 먼저 만든다.
