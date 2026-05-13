# 너나사 (YouBuyFirst) 작업 목록

## 완료된 초기 MVP 작업

- [x] Spring Boot ingestion API 추가
- [x] MySQL/Flyway schema 추가
- [x] Swagger admin 조회 API 추가
- [x] Python worker skeleton 추가
- [x] 네이버 종토방 crawler adapter 추가
- [x] 에펨코리아 crawler adapter 추가
- [x] crawler fixture test 추가
- [x] 종목 별칭 matcher 추가
- [x] LLM provider abstraction 추가
- [x] Docker Compose 로컬 실행 구성
- [x] 프로젝트 공통 기획/에이전트 문서 추가
- [x] GitHub Actions CI 추가
- [x] 작업 단위 문서 체계 추가
- [x] 최종 제품 기획안 문서 추가
- [x] 프로젝트명/런타임 식별자를 너나사 (YouBuyFirst) 기준으로 정리
- [x] PR 본문을 사람이 읽기 쉬운 결과 중심 형식으로 개선
- [x] Notion 작업일지/트러블슈팅 허브 생성
- [x] Notion 허브와 PR 템플릿을 B + A 하이브리드 UI 구조로 개선
- [x] 최종 기획에 커뮤니티별 수익률 비교 에이전트 반영
- [x] 크롤링 리스크 사례와 공개 배포 정책 문서화
- [x] 병렬 작업 트랙 문서 추가
- [x] GitHub/PR/Notion 병렬 작업 트랙 표시 기준 추가
- [x] 프론트 lane과 market 내부 lane 기준 추가
- [x] 프론트를 `frontend-experience` 독립 트랙으로 분리
- [x] 의존도에 따른 `main`/`track/*` 하이브리드 브랜치 전략 정리
- [x] PR/Notion 카드형 기록과 라벨/태그 사전 정리
- [x] AGENTS 범위 설명과 PR 라벨/문장 체계 정리
- [x] GitHub CLI 인증 확인
- [x] GitHub remote 연결
- [x] 첫 bootstrap PR 생성
- [x] 첫 bootstrap PR merge

## 지금 가장 가까운 작업

- [x] 사용자용 스크립트 제거와 한국어 PR 컨벤션 정리
- [ ] 실제 네이버 종토방 HTML 구조에 맞춘 parser 보강
- [ ] 실제 에펨코리아 주식 게시판 구조에 맞춘 parser 보강
- [ ] 종목 게시판형 수집을 위한 `CrawlTarget` 최소 설계
- [ ] 소스별 활성화 상태(`enabled`, `public-demo-only`, `local-research-only`, `disabled`) 설계
- [ ] `frontend-experience` 트랙에서 첫 대시보드 정보 구조와 mock 화면 설계
- [ ] `market-simulation-engine` market-data lane에서 quote snapshot 계약 설계
- [ ] worker가 backend readiness를 기다린 뒤 첫 배치를 실행하도록 개선
- [ ] `POST /internal/ingestions/community-posts` payload 예시를 Swagger에 추가

## 다음 MVP 작업 후보

- [ ] 종목 마스터 CSV를 국내 전체 + 미국 주식/ETF 데이터로 확장
- [ ] crawl run 실패/차단 원인별 backoff 정책 세분화
- [ ] retention cleanup 테스트 추가
- [ ] 사용자용 sentiment ranking API 추가
- [ ] 30분 집계 산식 검증 테스트 추가
- [ ] 커뮤니티별 수익률 비교 에이전트 데이터 모델 설계
- [ ] 공개 배포 가능한 시세 provider 조사
- [ ] Docker Compose smoke test 정리

## 최종 제품 후순위 작업

- [ ] 감성 대시보드 UI
- [ ] 감성 지표와 시세를 함께 보여주는 투자 참고 화면
- [ ] AI 3줄 요약
- [ ] 커뮤니티별 수익률 비교 에이전트
- [ ] 모의투자 주문/체결 엔진
- [ ] AI 에이전트 배틀
- [ ] OCR 자산 연동
- [ ] S3 Presigned URL 업로드
- [ ] Redis quote cache
- [ ] WebSocket 실시간 가격 브로드캐스트
- [ ] Spring Security 인증/인가
- [ ] 운영 배포와 모니터링

## Agent Notes

- 작업 단위는 하나의 체크박스 또는 강하게 묶인 2-3개 체크박스로 제한합니다.
- 작업을 시작하면 `codex/<task-name>` 브랜치에서 진행합니다.
- 구현 전에 관련 테스트를 먼저 추가하거나 기존 테스트를 확장합니다.
- PR 설명에는 변경 범위, 사람이 읽기 쉬운 검증 결과, 남은 리스크를 포함합니다.
- 여러 채팅으로 병렬 작업할 때는 `docs/workstreams/README.md`와 해당 트랙 문서를 먼저 읽고 서로 다른 파일/모듈을 소유하도록 나눕니다.
