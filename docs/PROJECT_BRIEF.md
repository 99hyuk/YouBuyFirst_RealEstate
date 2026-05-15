# 너나사 (YouBuyFirst) 프로젝트 기획 요약

## 현재 MVP 설명

현재 MVP는 대시보드나 모의투자가 아니라, 신뢰 가능한 데이터 파이프라인입니다. 네이버 종토방과 에펨코리아에서 신규 글을 수집하고, 국내 주식과 미국 상장 주식/ETF 언급을 인식한 뒤, 종목별 언급량과 커뮤니티 반응 신호를 저장합니다.

## MVP 목표

- 네이버 종토방과 에펨코리아에서 신규 글 묶음을 30분 주기로 수집
- 국내 종목과 미국 상장 주식/ETF를 종목 마스터로 인식
- 게시글별 종목 언급 추출
- LLM provider를 통해 종목별 반응 방향을 `bullish`, `bearish`, `neutral`로 분류
- Spring Boot ingestion API로 저장
- Swagger admin API로 수집 상태, 게시글, 종목별 metrics 확인

## 수집 전략 보정

30분 집계는 MVP의 핵심이므로 유지합니다. 다만 소스 구조에 따라 수집 방식을 나눕니다.

- 에펨코리아 같은 일반 게시판형 소스는 최근 글 목록을 수집한 뒤 글 안에서 종목을 인식합니다.
- 네이버 종토방 같은 종목 게시판형 소스는 종목별 게시판을 모두 전수 순회하지 않고, 우선순위가 있는 `CrawlTarget` 큐로 관리합니다.
- 초기 구현은 로컬/시연 가능한 범위에서 시작하고, 공개 배포 시에는 소스별 `enabled`, `public-demo-only`, `local-research-only`, `disabled` 상태를 둡니다.
- 공개 화면은 원문보다 집계 지표, 대표 키워드, 반응 방향 비율, AI 재서술 근거를 중심으로 설계합니다.

## 확정 설계 결정

- Spring Boot가 중심 시스템이며 저장, 검증, 중복 제거, admin API를 담당합니다.
- Python pipeline은 크롤링, Playwright fallback, LLM 분석을 담당합니다.
- LLM provider는 추상화하고, 기본 구현은 OpenAI adapter로 둡니다.
- `OPENAI_API_KEY`가 없으면 mock provider로 로컬 시연을 가능하게 합니다.
- 차단된 소스는 우회하지 않고 crawl run 실패 상태로 기록합니다.
- 제한 원문 보관 기간은 30일입니다.
- MySQL host port는 로컬 충돌을 피하기 위해 `3307`을 사용합니다.
- 로그인, CAPTCHA, 프록시, fingerprint 우회는 MVP뿐 아니라 최종 기획에서도 하지 않습니다.

## MVP에서 제외

- 사용자용 대시보드
- AI 3줄 요약
- OCR 자산 연동
- AI vs 유저 모의투자
- Spring Security 기반 인증/인가
- 전체 종목 마스터 자동 동기화
- AWS 배포와 운영 모니터링
- 커뮤니티별 수익률 비교 에이전트 구현
- 시세/호가 provider 실제 연동

## 최종 제품 방향

최종 제품은 `docs/FINAL_PRODUCT_PLAN.md`를 기준으로 합니다. 현재 MVP는 그 최종 제품의 첫 번째 기반 작업인 커뮤니티 반응 신호 수집/저장 파이프라인입니다.

최종 제품에는 커뮤니티별 수익률 비교 에이전트, 시세/호가 기반 투자 참고 화면, 모의투자/AI 에이전트, OCR 자산 연동이 포함됩니다. 커뮤니티 분석 용어와 소스별 수집 전략은 `docs/COMMUNITY_REACTION_GUIDE.md`를 기준으로 하고, 병렬 작업 트랙은 `docs/workstreams/README.md`를 기준으로 나눕니다.
