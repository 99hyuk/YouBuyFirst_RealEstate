# 부동산 AI 분석 워크플로우 결정

작성일: 2026-06-11

## 결론

MVP에서는 AI 분석을 Spring 요청 흐름 안에서 즉시 실행하지 않는다.

기본 구조는 `Python pipeline -> Spring Boot 저장/API -> Vue 화면 조회`로 둔다. Python pipeline은 크롤링, 별칭 매칭, 반응 분류, 쟁점 분류, AI 리포트/evidence log 생성을 맡고, Spring Boot는 작업 요청, DB 저장, 트랜잭션, 화면 조회 API를 맡는다.

LangGraph는 초기 필수 엔진으로 쓰지 않는다. 다만 지역/단지 상세 리포트처럼 분기, 재시도, guardrail, human review, evidence log 저장이 필요한 분석에는 `RealEstateEvaluationGraph` 파일럿으로 도입할 수 있다.

제품 정체성은 `수요자 반응 기반 부동산 시장 해석 서비스`입니다. 에이전트는 언급량 지표, 반응 방향, 쟁점 비율, 표본 신뢰도, 유사 과거, 최근 이슈, 시장 사실을 함께 보고 지역/단지 평가와 근거 로그를 남깁니다.

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
| Vector DB | 과거 유사 반응 window와 이후 시장 흐름 검색 | 간접 |
| GMS Gemini embedding | 커뮤니티/뉴스/반응 window 요약을 유사도 검색용 벡터로 변환 | 예 |
| SerpApi/search API | 최근 뉴스, 정책, 개발, 교통, 금리, 대출, 청약 이슈 후보 탐색 | 아니오 |
| LangGraph | 복잡한 리포트 생성 workflow의 상태/분기/재시도 관리 | 선택 |
| Langfuse | LLM 호출 관측, 품질/비용/지연 추적 | 아니오 |
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
   - reaction snapshot, market fact, policy event, content item, source coverage, 유사 과거, 최근 이슈 후보를 읽어 요약한다.
   - 결과는 `evidence_logs`, `evidence_log_items`에 저장한다.

5. 문구 guardrail 검사
   - 금지 표현: 추천, 사라, 매수 기회, 청약 넣어라, 대출 받아라, 무조건 오른다, 수익 보장 등.
   - 금지 표현이 나오면 재생성하거나 `skipReason`을 남긴다.

## 평가 입력과 출력

입력:

- 관심도: 최근 언급량, 증가율, 반복 언급 여부, source 다양성
- 반응 방향: 기대, 우려, 혼조, 관망
- 주요 쟁점: 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책, 개발 호재, 가격 부담, 실거주 만족도
- 유사 과거: 비슷한 반응 패턴과 이후 실거래/전세/매물 흐름
- 최근 이슈: 뉴스, 컬럼, 정책, 개발, 금리, 대출, 교통 이슈 후보
- 시장 사실: 실거래가, 전세가, 매물량, 청약, 정책 데이터와 `provider/asOf/stale`

출력:

- 대상: 지역 또는 단지
- 관심도 요약
- 반응 방향
- 주요 쟁점
- 유사 과거 비교
- 최근 이슈 후보
- 시장 사실 요약
- 종합 평가
- 근거 로그: 사용한 지표, 링크, snapshot id, 검색 provider, model version, prompt version

허용 표현:

- 관심이 빠르게 증가한 구간
- 기대와 우려가 함께 나타나는 구간
- 정책 이슈에 민감하게 반응하는 지역
- 과거 유사 상황에서는 변동성이 커졌던 패턴
- 실거래 흐름과 커뮤니티 반응이 아직 일치하지 않는 상태

금지 표현:

- 사라, 팔아라, 청약 넣어라, 지금 들어가라
- 오른다, 수익 보장, 확정 호재
- 대출 받아라, 매수 기회, 매도 신호

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

## 검색과 관측 도구의 경계

### SerpApi/search API

검색 API는 최근 이슈 후보와 근거 링크를 보강하는 보조 채널입니다. 검색 결과 수나 순위를 관심도 지표로 쓰지 않습니다. 저장 범위는 제목, 출처, 날짜, 링크, 관련 키워드, 검색 provider, query, target 후보 confidence 정도로 제한합니다.

현재 pipeline은 `realestate-recent-issues`와 `realestate-recent-issues-push` 명령으로 SerpApi Google News 결과를 후보 content item으로 변환합니다. `SERPAPI_API_KEY`는 로컬 환경변수 또는 `.env`에서만 읽고 repo에는 실제 값을 저장하지 않습니다. 후보는 `sourceId=serpapi:google_news`, `linkType=search_candidate`, `reviewState=candidate`, `dataStatus=candidate`로 저장되며 운영자 승인 전에는 target timeline 정본으로 보지 않습니다.

### Vector DB

벡터DB는 현재 window와 과거 window의 유사도를 찾는 분석 레이어입니다. target 식별, market fact 계산, 관심도 점수 산출의 정본이 아닙니다.

현재 MVP는 `realestate-similar-windows --similar-engine <batch|qdrant>` 한 명령 안에 두 검색 경로를 둡니다. 기본 `batch` engine은 reaction snapshot payload를 읽어 현재 window와 과거 window를 비교하고 반응 방향 비율, 언급 증가 패턴, heat score, issue overlap 기준으로 `similarityScore`를 계산합니다. 의미 기반 `qdrant` engine은 Qdrant adapter를 통해 `realestate-embeddings` 출력 벡터를 검색합니다.

임베딩 모델은 GMS의 `gemini-embedding-2`를 기본 후보로 둡니다. 호출 경로는 `https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent`이며, 키는 Gemini 방식처럼 `x-goog-api-key: ${GMS_KEY}` 헤더로 전달합니다. 이 임베딩은 target 식별이나 가격 계산에 쓰지 않고, 과거 유사 반응 window, 뉴스/컬럼 후보, 쟁점 요약의 의미 기반 검색과 클러스터링에만 사용합니다.

Python pipeline은 대량 임베딩 batch와 벡터 저장소 적재를 맡고, Spring Boot는 저장된 유사 과거 검색 결과와 EvidenceLog 조회/저장을 맡습니다. 화면 요청 중 즉시 임베딩을 생성하지 않고, batch 결과의 `provider`, `modelName`, `asOf`, `stale` 상태를 함께 남깁니다.

현재 pipeline에는 `realestate-embeddings` 명령이 있습니다. `--reaction-snapshots-jsonl`로 reaction snapshot JSONL을 입력하면 각 window를 임베딩용 텍스트로 요약하고, `GMS_KEY`, `GMS_GEMINI_BASE_URL`, `GMS_GEMINI_EMBEDDING_MODEL` 환경변수를 사용해 GMS Gemini embedding API를 호출합니다. 출력 payload는 `inputId`, `targetId`, `refType=reaction_snapshot`, `provider=gms:gemini`, `modelName`, `text`, `embedding`, `dimensions`, `dataStatus=generated`를 포함합니다. `realestate-vector-upsert`는 이 payload를 Qdrant collection에 저장합니다. `realestate-similar-windows --similar-engine qdrant --embeddings-jsonl ... --vector-source-input-id ...`는 특정 `inputId`의 vector로 유사 window를 검색해 EvidenceLog에 바로 넣을 수 있는 `similar_window` item shape를 출력합니다.

운영 smoke는 `realestate-vector-health`로 확인합니다. 이 명령은 Qdrant collection의 `ready`, `status`, `pointsCount`, `vectorsCount`를 secret 없이 출력합니다. `status=missing`이면 아직 운영 collection이 만들어지지 않은 상태이므로 `realestate-vector-upsert`로 collection 생성과 임베딩 포인트 적재를 먼저 수행합니다. `ready=false`가 계속되면 Qdrant runtime, collection 이름(`REALESTATE_VECTOR_COLLECTION`), 네트워크, API key 설정을 점검한 뒤 유사 과거 검색 batch를 실행합니다.

`--similar-market-facts-jsonl`을 함께 주면 matched window 이후 지정 horizon 안의 market fact 흐름을 `afterMarketSummary`로 붙입니다. 예를 들어 과거 window 이후 `apt_trade.dealAmountManwon`의 첫 값과 마지막 값을 비교해 `deltaPct`를 기록합니다. 이 값은 "이후 실제 시장 사실 흐름"을 보강하는 근거 후보이며, 가격 상승/하락의 원인 단정이나 행동 지시로 쓰지 않습니다.

출력된 후보는 `evidenceItems[]`에 `evidenceType=similar_window`, `refType=similar_window`로 연결할 수 있습니다. batch와 Qdrant engine 모두 이 shape를 유지하므로 `realestate-evidence-logs --evidence-similar-windows-jsonl <similar-window-output>` 경로로 같은 EvidenceLog 생성 흐름을 재사용합니다.

### EvidenceLog 생성 command

현재 pipeline은 `realestate-evidence-logs`와 `realestate-evidence-logs-push` 명령으로 반응 snapshot, market fact, timeline event, SerpApi/search 후보 content item, 유사 과거 window 후보를 하나의 EvidenceLog payload로 조립합니다.

- `realestate-evidence-logs`는 JSON으로 `logs[]`를 출력합니다.
- `realestate-evidence-logs-push`는 같은 payload를 `POST /internal/realestate/evidence-logs`로 전송합니다.
- `--evidence-timeline-events-jsonl`은 `GET /api/realestate/targets/{targetId}/timeline` 응답 shape의 JSON/JSONL을 받아 `evidenceType=timeline_event`, `refType=timeline_event` 항목으로 연결합니다.
- 현재 summary/tone은 룰 기반 baseline입니다. LLM provider를 붙이더라도 `evidenceLogId`, `evidenceItems[]`, `caveats`, `dataQuality`, `evaluationVersion`, `promptVersion`, `modelName` shape는 유지합니다.
- `--evidence-use-gms-llm`을 켜면 GMS OpenAI-compatible chat endpoint를 호출해 baseline EvidenceLog의 `summary`, `subtitle`, `tone`만 보강합니다. 기본 모델은 `gpt-5-mini`이며, `GMS_KEY`, `GMS_OPENAI_BASE_URL`, `GMS_OPENAI_CHAT_MODEL` 환경변수 또는 CLI 옵션으로 조정합니다.
- LLM 결과에 `사라`, `팔아라`, `청약 넣어라`, `지금 들어가라`, `오른다`, `수익 보장`, `확정 호재`, `대출 받아라`, `매수 기회`, `매도 신호` 같은 금지 표현이 있으면 해당 문구를 저장하지 않고 룰 기반 문구를 유지합니다. 이때 `skipReason=forbidden_copy_detected`와 caveat을 남깁니다.
- 입력 근거가 부족하면 `market_fact_missing`, `timeline_event_missing`, `similar_window_missing`, `search_candidate_missing` caveat을 남깁니다.
- 문구는 "관찰됩니다", "함께 나타납니다"처럼 관찰형으로 제한하고 행동 지시 표현은 쓰지 않습니다.

일일 자동 refresh에서는 `serve --enable-realestate-daily-refresh --enable-realestate-evidence-logs-refresh`를 사용합니다. 이 step은 backend의 최신 `GET /api/realestate/reactions/rankings` 결과를 기준으로 target을 고르고, 각 target의 `market-facts`, `timeline`, `content` API를 읽어 EvidenceLog를 생성한 뒤 `POST /internal/realestate/evidence-logs`로 저장합니다. `--evidence-similar-windows-jsonl`을 함께 주면 미리 생성한 batch/Qdrant 유사 과거 후보 중 현재 target/window와 맞는 항목을 `similar_window` 근거로 병합합니다. `--evidence-use-gms-llm`을 함께 켜면 같은 step 안에서 GMS LLM summary 보강과 forbidden copy guardrail을 적용합니다. 최신 ranking이 비어 있으면 `EMPTY`로 끝나며, 기존 EvidenceLog를 덮어쓰지 않고 `evaluatedAt` 기준의 새 평가 로그를 남깁니다.

### Langfuse

Langfuse는 판단 로직 자체가 아닙니다. 실제 판단의 정본은 우리 DB에 저장되는 `evidence_logs`, `reaction_snapshots`, `timeline_events`, 유사 과거 검색 결과입니다. Langfuse는 LLM 호출을 관측하고 검증하는 도구로만 사용합니다.

추적 후보:

- prompt version
- model name
- 입력 snapshot id
- 참고한 검색 결과와 vector search result id
- latency
- cost
- guardrail 결과
- 평가 품질 태그

## Spring API 후보

Spring은 AI를 직접 실행하기보다 작업과 결과를 관리한다. 현재 EvidenceLog 저장/조회는 구현되어 있고, analysis job과 최종 evaluation summary API는 후속 후보입니다.

```text
POST /api/realestate/analysis-jobs
GET  /api/realestate/analysis-jobs/{jobId}
GET  /api/realestate/targets/{targetId}/evidence-logs
POST /internal/realestate/evidence-logs
GET  /api/realestate/targets/{targetId}/evaluation
POST /api/admin/realestate/mention-reviews/{mentionId}
```

구현된 EvidenceLog 저장 API는 pipeline 또는 배치 분석기가 만든 평가 로그를 DB 정본으로 남깁니다. `evidenceLogId` 기준 upsert이며, `targetId`, `evaluationVersion`, `promptVersion`, `modelName`, `tone`, `summary`, `subtitle`, `caveats`, `dataQuality`, `confidence`, `skipReason`, `evaluatedAt`, `asOf`, `evidenceItems[]`를 받습니다. `snapshotId`는 있으면 `real_estate_reaction_snapshots.id`를 참조합니다.

`evidenceItems[]`는 반응 snapshot, market fact, timeline event, content item, 검색 후보, 후속 유사 과거 결과 같은 근거 조각을 연결합니다. 저장 필드는 `evidenceItemId`, `evidenceType`, `refType`, `refId`, `label`, `valueText`, `severity`입니다. 내부 추론 전문은 저장하지 않고, 화면과 검수에 필요한 근거 요약과 참조 id만 남깁니다.

## 저장해야 할 최소 결과

```json
{
  "targetId": "target-id",
  "windowStart": "2026-06-11T00:00:00+09:00",
  "windowEnd": "2026-06-11T01:00:00+09:00",
  "evaluationVersion": "realestate-eval-v1",
  "promptVersion": "realestate-eval-prompt-v1",
  "model": "gpt-4.1-mini",
  "tone": "watch",
  "summary": "전세 우려와 교통 기대가 동시에 관찰됩니다.",
  "evidence": [],
  "similarWindows": [],
  "recentIssues": [],
  "caveats": ["market_fact_stale"],
  "dataQuality": "partial",
  "confidence": 0.72,
  "skipReason": null,
  "asOf": "2026-06-11T01:03:00+09:00"
}
```

## 다음 작업

1. `realestate-eval-v1` 입력/출력 JSON schema를 확정한다.
2. `pipeline/src/youbuyfirst_pipeline/realestate_reaction_classifier.py`의 룰 기반 baseline을 검증 데이터로 보강한다.
3. 기존 `pipeline/src/youbuyfirst_pipeline/llm.py`의 target mention prompt를 부동산 target mention prompt로 분리한다.
4. `MockRealEstateAIProvider`와 `OpenAIRealEstateAIProvider`를 만들고, 출력은 `realestate-reaction-observations`와 같은 observation shape로 맞춘다.
5. Spring에 analysis job 상태 모델을 추가할지, pipeline이 직접 ingestion API로 밀지 결정한다.
6. Python pipeline에서 생성한 평가 결과를 `POST /internal/realestate/evidence-logs`로 전송하는 명령을 만든다. 완료: `realestate-evidence-logs(-push)`.
7. forbidden copy guardrail 테스트를 만든다.
8. `realestate-similar-windows` 결과를 EvidenceLog 생성 command에 자동 병합한다. 완료: `--evidence-similar-windows-jsonl`.
9. 상세 timeline event를 EvidenceLog 생성 command와 daily refresh에 자동 병합한다. 완료: `--evidence-timeline-events-jsonl`, `GET /api/realestate/targets/{targetId}/timeline`.
10. LangGraph는 위 함수 체인이 복잡해진 뒤 `RealEstateEvaluationGraph`로 전환한다.

## 보류 사항

- Spring AI 도입은 보류한다. Java 내부에서 간단한 관리자 요약이나 on-demand preview가 필요해질 때 재검토한다.
- LangGraph 도입은 보류한다. evidence log 생성 workflow가 분기/재시도/검수 상태를 실제로 요구할 때 파일럿으로 시작한다.
- 화면 요청 중 즉시 AI 호출은 하지 않는다. 예외가 필요하면 별도 cache/asOf/stale 정책을 먼저 만든다.
