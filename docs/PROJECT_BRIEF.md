# 너나사 (YouBuyFirst) 프로젝트 기획 요약

## 현재 MVP 설명

현재 MVP는 대시보드나 모의투자가 아니라, 신뢰 가능한 데이터 파이프라인입니다. 네이버 종토방과 에펨코리아에서 신규 글을 수집하고, 국내 주식과 미국 상장 주식/ETF 언급을 인식한 뒤, 종목별 언급량과 투자 심리를 저장합니다.

## MVP 목표

- 네이버 종토방과 에펨코리아에서 신규 글 묶음을 30분 주기로 수집
- 국내 종목과 미국 상장 주식/ETF를 종목 마스터로 인식
- 게시글별 종목 언급 추출
- LLM provider를 통해 종목별 `bullish`, `bearish`, `neutral` 감성 분석
- Spring Boot ingestion API로 저장
- Swagger admin API로 수집 상태, 게시글, 종목별 metrics 확인

## 확정 설계 결정

- Spring Boot가 중심 시스템이며 저장, 검증, 중복 제거, admin API를 담당합니다.
- Python worker는 크롤링, Playwright fallback, LLM 분석을 담당합니다.
- LLM provider는 추상화하고, 기본 구현은 OpenAI adapter로 둡니다.
- `OPENAI_API_KEY`가 없으면 mock provider로 로컬 시연을 가능하게 합니다.
- 차단된 소스는 우회하지 않고 crawl run 실패 상태로 기록합니다.
- 제한 원문 보관 기간은 30일입니다.
- MySQL host port는 로컬 충돌을 피하기 위해 `3307`을 사용합니다.

## MVP에서 제외

- 사용자용 대시보드
- AI 3줄 요약
- OCR 자산 연동
- AI vs 유저 모의투자
- Spring Security 기반 인증/인가
- 전체 종목 마스터 자동 동기화
- AWS 배포와 운영 모니터링

## 최종 제품 방향

최종 제품은 `docs/FINAL_PRODUCT_PLAN.md`를 기준으로 합니다. 현재 MVP는 그 최종 제품의 첫 번째 기반 작업인 커뮤니티 감성 수집/저장 파이프라인입니다.
