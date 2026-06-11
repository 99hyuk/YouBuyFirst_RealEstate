# 부동산 커뮤니티/source 후보

작성일: 2026-06-11

## 결론

부동산 반응 수집은 처음부터 30개 adapter를 만들지 않는다.

먼저 공개 접근성이 높고 글 흐름이 빠른 게시판형 source 2-3곳을 P0로 검증하고, 규모가 큰 네이버/다음 카페와 앱 커뮤니티는 `disabled` 또는 `local-research-only` 상태로 source registry에 올린 뒤 공개 목록 접근성, robots/약관, 로그인 필요 여부를 확인한다.

초기 운영 기준:

1. P0: 공개 게시판형 최신글 목록을 확인할 수 있는 source
2. P1: 이용자 규모나 영향력은 크지만 카페/앱/로그인 검증이 필요한 source
3. P2: 뉴스, 컬럼, 앱 정보, 공공/시장 fact처럼 반응 분석을 보조하는 source

이 문서는 "수집 승인 목록"이 아니라 "후보 목록"이다. `crawlPolicyCandidate`가 `public-http-candidate`여도 adapter 구현 전에는 source별 정책 검토가 필요하다.

## 우선 검증 후보

| sourceId | 이름 | 유형 | 후보 정책 | 신호 | 우선순위 | 확인 근거 |
| --- | --- | --- | --- | --- | --- | --- |
| `ppomppu_house` | 뽐뿌 부동산포럼 | 공개 게시판 | `public-http-candidate` | 내집마련, 계약, 이사, 대출, 전세 이슈 | P0 | 공식 목록에 부동산포럼과 최신글 노출 |
| `dc_immovables` | 디시인사이드 부동산 갤러리 | 공개 게시판 | `public-http-candidate` | 빠른 감정 반응, 지역/정책 논쟁, 과열/우려 신호 | P0 | 공식 갤러리 목록에 게시글 번호, 작성일, 조회/추천 노출 |
| `hogangnono_community` | 호갱노노 이야기 | 앱/웹 커뮤니티 | `local-research-only` | 실거주 후기, 아파트 단지 단위 체감 | P0 | 공식 커뮤니티 페이지와 직방 보도자료에서 이야기 탭 운영 확인 |
| `blind_realestate_topic` | 블라인드 부동산 토픽 | 직장인 커뮤니티 | `local-research-only` | 직장인 실수요, 고소득권역, 대출/갈아타기 고민 | P1 | 공개 토픽 페이지와 게시글 일부 확인. 앱/로그인 의존성 검토 필요 |
| `naver_boodongsan_study` | 부동산스터디 | 네이버 카페 | `disabled` | 시장 심리, 정책 반응, 지역별 논쟁 | P1 | 언론에서 대형 부동산 카페 영향력과 회원 규모 언급 |
| `naver_peterpanz` | 피터팬의 좋은방 구하기 | 네이버 카페/앱 | `disabled` | 전월세, 직거래, 거주 후기, 임차 수요 | P1 | 카페 회원 300만 돌파와 거주/거래 후기 제공 언급 |
| `naver_rainup` | 아름다운 내집갖기 | 네이버 카페 | `disabled` | 내집마련, 재테크, 지역/단지 관심 | P1 | 카페 소개와 100만 회원 관련 공개 근거 확인 |
| `wolbu_cafe` | 월급쟁이부자들 | 네이버 카페/교육 커뮤니티 | `disabled` | 투자 학습 커뮤니티, 유튜브/카페 기반 관심 흐름 | P1 | 2026년 언론에서 유튜브 210만, 온라인 카페 64만 언급 |
| `daum_happytech` | 행복재테크 | 다음 카페 | `disabled` | 경매, 공매, 재테크, 투자자 반응 | P1 | 다음 프리미엄 우수카페 선정과 회원 규모 관련 언론 근거 |
| `asil_app` | 아실 | 앱/웹 정보 서비스 | `local-research-only` | 실거래, 순위, 개발정보, 사용자 관심 지역 | P2 | Google Play/App Store 설명에서 다운로드와 기능 확인 |

## 30개 내외 registry 확장 슬롯

아래는 바로 크롤러를 만들 목록이 아니라 source registry의 `disabled` 후보를 채우기 위한 슬롯이다. 실제 이름과 URL은 공개 접근성 확인 뒤 확정한다.

| 그룹 | 슬롯 | 목적 | 초기 상태 | 확인할 것 |
| --- | --- | --- | --- | --- |
| 공개 게시판형 | 3-5개 | 최신글 기반 반응 흐름 | `disabled` | 목록 URL, page/cursor, 작성시각, 조회/댓글 필드 |
| 대형 부동산 카페 | 8-10개 | 투자/내집마련 심리 | `disabled` | 비로그인 공개 목록 여부, 검색 노출, 카페별 게시판 구조 |
| 지역/맘카페 | 8-10개 | 생활권, 학군, 전세, 신축 선호 | `disabled` | 지역별 공개 게시판 여부, 부동산 글 비중, 운영 정책 |
| 앱/프롭테크 커뮤니티 | 3-5개 | 단지 후기와 거주자 체감 | `local-research-only` | 웹 공개 페이지 여부, deep link, 원문 저장 제한 |
| 뉴스/컬럼/공식 공지 | 6-8개 | 정책/교통/공급 이벤트 보조 | `disabled` | 제목/link/snippet 저장 가능성, 원문 재게시 금지 |
| 공공/시장 fact | 5-8개 | 실거래, 전월세, 지수, 미분양 | `local-research-only` | 공식 API, 갱신 지연, provider/asOf/stale 기준 |

## 수집 정책 메모

- 네이버/다음 카페는 규모가 커도 로그인, 가입 승인, 검색 제한이 있으면 자동 수집 대상에서 제외한다.
- 블라인드는 공개 웹으로 일부 글과 토픽이 보이지만 앱/로그인 의존성이 크므로 P0 crawler가 아니라 P1 검토 source로 둔다.
- 호갱노노/아실 같은 앱 기반 source는 웹 공개 범위가 좁을 수 있으므로, 원문 수집보다 단지/지역 관심 신호와 링크 근거 중심으로 검토한다.
- 지역/맘카페는 생활권 신호가 강하지만 사적 대화와 개인정보 리스크가 커서 공개 게시판 확인 전까지 adapter를 만들지 않는다.
- 뉴스/컬럼은 커뮤니티 반응이 아니라 정책/이벤트/쟁점 근거로만 쓴다.

## P0 spike 순서

1. `ppomppu_house` 최신글 목록 parser spike
2. `dc_immovables` 최신글 목록 parser spike
3. `hogangnono_community` 공개 웹 범위 확인
4. 위 3곳의 source registry 필드 확정
5. source별 `blocked`, `failed`, `partial`, `complete` coverage 샘플 작성

## source registry 필드 후보

```json
{
  "sourceId": "ppomppu_house",
  "displayName": "뽐뿌 부동산포럼",
  "sourceType": "general_board",
  "primaryUrl": "https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1",
  "targetScope": ["region", "complex", "policy_area"],
  "crawlPolicy": "disabled",
  "policyReviewState": "pending",
  "requiresLogin": false,
  "publicListObserved": true,
  "allowedStorage": ["title", "contentSnippet", "url", "authorHash", "publishedAt", "contentHash"],
  "adapterStatus": "not_started",
  "priority": "P0"
}
```

## 다음 작업

1. 위 후보를 `crawl_sources` seed 후보로 옮긴다.
2. P0 2-3곳만 실제 HTML 샘플을 저장하고 parser 테스트를 만든다.
3. 네이버/다음 카페는 공개 목록 접근성 확인 결과에 따라 `excluded-login-required` 또는 `local-research-only`로 분리한다.
4. 지역/단지 alias DB 초안과 연결해, source별로 어떤 별칭이 많이 필요한지 기록한다.
5. source skew가 큰 source는 지표 산식에서 가중치를 낮추거나 별도 caveat를 붙인다.

## 외부 확인 근거

- 뽐뿌 부동산포럼: https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1
- 디시인사이드 부동산 갤러리: https://gall.dcinside.com/board/lists/?id=immovables
- 블라인드 부동산 토픽: https://www.teamblind.com/kr/topics/%EB%B6%80%EB%8F%99%EC%82%B0
- 호갱노노 커뮤니티: https://hogangnono.com/community
- 호갱노노 이야기 개편 보도자료: https://company.zigbang.com/newsroom/view?idx=339
- 부동산스터디 관련 언론: https://www.sedaily.com/article/12892140
- 피터팬 카페 회원 300만 관련 언론: https://www.sentv.co.kr/article/view/sentv202402190072?d=pc
- 월급쟁이부자들 관련 언론: https://realty.chosun.com/site/data/html_dir/2026/02/20/2026022002804.html
- 아름다운 내집갖기 소개: https://eparajoo.com/real_estate-blog/?bmode=view&idx=7379356
- 행복재테크 관련 언론: https://www.lawissue.co.kr/view.php?ud=20180303021621903107f28b58b8_12
- 아실 Google Play: https://play.google.com/store/apps/details?hl=ko&id=kr.co.koreachart.city
- 국토교통부 실거래가 공개시스템 자료제공: https://rt.molit.go.kr/pt/xls/xls.do?mobileAt=
