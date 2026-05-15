# Work Unit: Crawl Parser Robustness

## Goal

네이버 종토방과 에펨코리아 주식 게시판의 실제 목록 HTML 구조를 더 잘 읽도록 crawler parser와 fixture 테스트를 보강한다.

## Scope

- 네이버 종토방 목록 행에서 날짜 칸이 제목 앞에 오는 구조를 처리한다.
- 네이버 작성자 칸을 조회수/추천수와 구분해 읽는다.
- 에펨코리아 공지 행은 제외하고, `/123` 형식과 `document_srl=123` query 형식의 게시글 링크를 모두 처리한다.
- 에펨코리아 date-only 표기인 `26.05.15`를 KST 기준 날짜로 파싱한다.
- 실제 구조를 짧게 재현한 crawler fixture를 추가한다.

## Out of Scope

- 로그인, CAPTCHA, 프록시, fingerprint 우회
- backend ingestion contract 변경
- 종목 인식, 반응 방향 분류, 화면, 시세, 모의투자
- 원문 대량 저장 또는 실제 커뮤니티 HTML 원본 보관

## Verification

- Docker Python 3.10 환경에서 pipeline 전체 `pytest` 20개 통과를 확인했다.
- `git diff --check` 통과를 확인했다.

## Notes

fixture는 실제 페이지 전체가 아니라 목록 행 구조만 재현한 짧은 샘플이다. 공개 HTTP 샘플은 구조 확인 용도로만 사용했고, 우회나 로그인 접근은 하지 않았다.
