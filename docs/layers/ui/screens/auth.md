# Auth

## Route

- Parent: app shell
- Route 정보: `/auth/login`, `/auth/register`, `/auth/find-account`
- Child screens: 없음

## 화면 목적

사용자가 세션 기반 계정으로 로그인하거나 회원가입해서 상단 계정 상태와 채팅 참여 상태를 사용자 세션 기준으로 관리할 수 있게 한다. 로그인, 회원가입, ID/PW 찾기는 서로 다른 화면으로 둔다.

## 현재 섹션

- 로그인 화면: 아이디와 비밀번호 입력 후 `/api/auth/login` 호출. 성공하면 `/dashboard`로 이동한다. 하단에 회원가입과 ID/PW 찾기 링크를 둔다.
- 회원가입 화면: 아이디, 이메일, 닉네임, 비밀번호 입력 후 `/api/auth/register` 호출. 성공하면 `/dashboard`로 이동한다.
- 간편 로그인/회원가입: Google, Naver, Kakao 버튼은 `/api/auth/oauth/providers`에서 `configured=true`인 provider만 `/oauth2/authorization/{provider}` 링크로 이동한다. 로그인 화면의 provider 버튼은 각 사이트 아이콘을 사용한 3개 가로 배열로 둔다. 설정되지 않은 provider는 비활성 버튼으로 보여주고 Whitelabel 404 경로로 보내지 않는다. provider 인증 성공 후 백엔드가 `JSESSIONID`를 만들고 `/dashboard`로 돌려보낸다.
- ID/PW 찾기 화면: 이메일과 아이디 입력 폼을 분리해서 둔다. 실제 복구 API 연결 전까지 제출은 비활성 상태다.
- 상단 계정 상태: 로그인 전에는 `/auth/login` 링크, 로그인 후에는 `닉네임님 안녕하세요`와 로그아웃 버튼 표시.
- 계정 플로우의 주요 폼은 화면 중앙에 배치하고, 활성 버튼은 hover/focus 상태가 보여야 한다.

## 상태와 빈 화면

- loading: 버튼 문구를 `확인 중`, `생성 중`으로 바꾸고 중복 제출을 막는다.
- empty: 로그인 전 상단에는 로그인 링크만 표시한다.
- error: API 오류 문구를 각 폼 하단에 표시한다.
- stale/mock: 계정 화면에는 사용자 저장 목록처럼 보이는 mock 데이터를 표시하지 않는다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `username` | backend auth | 영문/숫자 4-20자, 로그인 ID, unique |
| `password` | backend auth | 회원가입 시 영문/숫자/특수문자 포함 8자 이상 |
| `email` | backend auth | unique 이메일 |
| `displayName` | backend auth | unique 닉네임, 상단 인사 표시 |
| `oauthProvider` | backend auth | Google/Naver/Kakao OAuth 시작 경로와 provider identity 연결 |
| `oauthProviders` | backend auth | `/api/auth/oauth/providers` 응답. provider별 `displayName`, `authorizationUrl`, `configured`로 버튼 활성 여부 결정 |

## 기획 확인 필요

- 비밀번호 찾기/이메일 인증은 아직 범위 밖.
- OAuth provider client id/secret이 없는 로컬 환경에서는 간편 로그인/회원가입 버튼이 비활성 상태다.

## 변경 로그

- 2026-06-23: 세션 로그인 프론트 연결, 회원가입 양식 제한, 상단 로그인/로그아웃 상태 기준 추가.
- 2026-06-23: 로그인 화면에서 회원가입 폼을 분리하고 `/auth/register`, `/auth/find-account` 라우트 추가. 로그아웃 hover/focus 상태 추가.
- 2026-06-23: 로그인/회원가입/ID-PW 찾기 폼 중앙 정렬과 계정 플로우 버튼 hover/focus 기준 추가.
- 2026-06-25: 마이페이지 route 제거에 맞춰 로그인/회원가입 성공 후 이동 경로를 `/dashboard`로 변경.
- 2026-06-25: Google/Naver/Kakao OAuth 진입 버튼과 provider 인증 후 세션 로그인 흐름을 추가.
- 2026-06-25: OAuth provider 설정 상태 API를 기준으로 미설정 provider 버튼을 비활성화해 Whitelabel 404 이동을 막음.
- 2026-06-25: 로그인 화면의 Google/Naver/Kakao OAuth 버튼을 아이콘형 가로 배열로 변경.
