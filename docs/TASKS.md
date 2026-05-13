# 인간지표 작업 목록

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
- [x] GitHub CLI 인증 확인
- [x] GitHub remote 연결
- [x] 첫 bootstrap PR 생성
- [x] 첫 bootstrap PR merge

## 지금 가장 가까운 작업

- [x] 사용자용 스크립트 제거와 한국어 PR 컨벤션 정리
- [ ] 실제 네이버 종토방 HTML 구조에 맞춘 parser 보강
- [ ] 실제 에펨코리아 주식 게시판 구조에 맞춘 parser 보강
- [ ] worker가 backend readiness를 기다린 뒤 첫 배치를 실행하도록 개선
- [ ] `POST /internal/ingestions/community-posts` payload 예시를 Swagger에 추가

## 다음 MVP 작업 후보

- [ ] 종목 마스터 CSV를 국내 전체 + 미국 주식/ETF 데이터로 확장
- [ ] crawl run 실패/차단 원인별 backoff 정책 세분화
- [ ] retention cleanup 테스트 추가
- [ ] 사용자용 sentiment ranking API 추가
- [ ] 30분 집계 산식 검증 테스트 추가
- [ ] Docker Compose smoke test 정리

## 최종 제품 후순위 작업

- [ ] 감성 대시보드 UI
- [ ] AI 3줄 요약
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
- PR 설명에는 변경 범위, 검증 명령, 남은 리스크를 포함합니다.
- 여러 채팅으로 병렬 작업할 때는 서로 다른 파일/모듈을 소유하도록 나눕니다.
