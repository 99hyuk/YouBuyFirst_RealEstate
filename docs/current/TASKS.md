# 너나사 (YouBuyFirst) 작업 목록

이 문서는 다음 행동을 고르기 위한 짧은 목록입니다. 완료 상세 이력은 PR, Notion 작업 로그, `docs/archive/work-units/items/`에서 찾습니다.

## 완료 요약

- ingestion MVP, 협업/PR 기반, 운영 기록 체계, 작업 영역 라벨 기준, ui/front shell은 main에 반영되어 있습니다.
- 최근 완료 상세는 PR/Notion 작업 로그와 `docs/archive/work-units/items/`에서 찾습니다.

## 지금 가장 가까운 작업

- [ ] ui/front shell 브라우저 QA와 기획자 확인 필요 항목 정리
- [ ] ui 메인 대시보드 와이어프레임 보강
- [ ] ui 관심종목 브리핑과 종목 이벤트 타임라인 와이어프레임 설계
- [ ] 관심종목, 최신 기사/공시, 신호 신뢰도 API 후보 설계
- [ ] 유튜브/신뢰 블로그/인기글 링크 카드와 종목 이벤트 타임라인 field 후보 설계
- [ ] pipeline이 backend `CrawlTarget` API를 사용하되 static target fallback을 유지하도록 연결
- [ ] admin target pause/resume/clear-backoff API와 화면 액션 연결
- [ ] 열린 브랜치/worktree를 active, review, blocked, stale, close-candidate로 분류하고 정리 후보 점검
- [ ] 기존 PR/Notion 카드 중 열려 있는 항목만 작업 영역 값으로 재분류
- [ ] Notion 과거 카드 대량 재분류는 도구 timeout을 피하도록 작은 묶음으로 진행
- [ ] `market` 영역에서 chart candles, quote snapshot, investor flows provider 안정화
- [ ] `simulation` 영역에서 모의 계좌, 주문, 체결, 원장 트랜잭션 최소 설계
- [ ] `agent` 영역에서 역발상 페르소나 입력 contract와 판단 key/idempotency 설계
- [ ] `community` 영역에서 뽐뿌 증권포럼, 디시 미국주식/주식갤러리/국내주식 계열 source registry 후보 정리
- [ ] `community` 영역에서 인기글/개념글 확산 레이어와 신뢰 블로그 whitelist 후보 정리
- [ ] 성능/품질 개선 사례가 실제로 생기면 개선 전후 수치와 측정 방법 기록
- [ ] backend 도메인 패키지 `instrument/sentiment/metrics`를 `stock/analysis/indicator`로 리네임
- [ ] pipeline 종목 매칭 모듈을 `stock` 기준 이름으로 정리
- [ ] pipeline이 backend readiness를 기다린 뒤 첫 배치를 실행하도록 개선
- [ ] `POST /internal/ingestions/community-posts` payload 예시를 Swagger에 추가

## 다음 MVP 후보

- [ ] 종목 마스터 CSV를 국내 전체 + 미국 주식/ETF 데이터로 확장
- [ ] retention cleanup 테스트 추가
- [ ] 사용자용 analysis ranking/indicator API 추가
- [ ] 관심종목 브리핑 API와 종목 이벤트 타임라인 API 설계
- [ ] 최신 기사/공시 메타데이터 수집 정책과 링크 표시 기준 정리
- [ ] 증권 유튜브, 신뢰 블로그, 인기글/개념글 외부 링크 표시 기준 정리
- [ ] 신호 신뢰도/주의 배지 산정 기준 정리
- [ ] 30분 집계 산식 검증 테스트 추가
- [ ] 실제 `OPENAI_API_KEY` 기반 AI mention resolver 샘플 품질 확인
- [ ] 커뮤니티별 성과 비교 snapshot 모델 설계
- [ ] 공개 배포 가능한 시세 provider 조사
- [ ] Docker Compose smoke test 정리
- [ ] 에이전트 paper trading 전략 계좌와 중복 판단 방지 규칙 설계

## 후순위 제품 작업

- [ ] 커뮤니티 반응 대시보드 UI
- [ ] 관심종목 브리핑
- [ ] 종목별 최신 기사/공시 리스트와 이벤트 타임라인
- [ ] 신호 신뢰도/주의 배지
- [ ] 반응 지표와 시세를 함께 보여주는 투자 참고 화면
- [ ] AI 3줄 요약
- [ ] 커뮤니티별 수익률 비교 paper trading 에이전트
- [ ] 모의투자 주문/체결/원장 트랜잭션 엔진
- [ ] AI 에이전트 배틀
- [ ] OCR 자산 연동
- [ ] S3 Presigned URL 업로드
- [ ] Redis quote cache
- [ ] WebSocket 실시간 가격 브로드캐스트
- [ ] Spring Security 인증/인가
- [ ] 운영 배포와 모니터링

## 작업 메모

- 작업 단위는 하나의 체크박스 또는 강하게 묶인 2-3개 체크박스로 제한합니다.
- 작업을 시작하면 `codex/<task-name>` 브랜치에서 진행합니다.
- 구현 전에 관련 테스트를 먼저 추가하거나 기존 테스트를 확장합니다.
- PR 설명에는 변경 범위, 사람이 읽기 쉬운 검증 결과, 남은 리스크를 포함합니다.
- 병렬 작업은 관련 도메인/layer `AGENTS.md`의 관련 섹션을 먼저 확인하고, 세부 색인이 필요할 때만 README를 봅니다. 작업 영역 경계가 헷갈릴 때만 `docs/layers/ops/WORK_AREAS.md`를 봅니다.
