# Auth

## Route

- Parent: app shell
- Route 정보: `/auth/login`, `/auth/register`, `/auth/find-account`
- Child screens: 없음

## 화면 목적

사용자가 세션 기반 계정으로 로그인하거나 회원가입해서 마이페이지의 저장 지역, 알림 조건, 관찰 메모를 사용자 계정 기준으로 관리할 수 있게 한다. 로그인, 회원가입, ID/PW 찾기는 서로 다른 화면으로 둔다.

## 현재 섹션

- 로그인 화면: 아이디와 비밀번호 입력 후 `/api/auth/login` 호출. 하단에 회원가입과 ID/PW 찾기 링크를 둔다.
- 회원가입 화면: 아이디, 이메일, 닉네임, 비밀번호 입력 후 `/api/auth/register` 호출.
- ID/PW 찾기 화면: 이메일과 아이디 입력 폼을 분리해서 둔다. 실제 복구 API 연결 전까지 제출은 비활성 상태다.
- 상단 계정 상태: 로그인 전에는 `/auth/login` 링크, 로그인 후에는 `닉네임님 안녕하세요`와 로그아웃 버튼 표시.
- 계정 플로우의 주요 폼은 화면 중앙에 배치하고, 활성 버튼은 hover/focus 상태가 보여야 한다.

## 상태와 빈 화면

- loading: 버튼 문구를 `확인 중`, `생성 중`으로 바꾸고 중복 제출을 막는다.
- empty: 로그인 전 상단에는 로그인 링크만 표시한다.
- error: API 오류 문구를 각 폼 하단에 표시한다.
- stale/mock: 사용자 계정 데이터에는 mock 저장 목록을 표시하지 않는다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `username` | backend auth | 영문/숫자 4-20자, 로그인 ID, unique |
| `password` | backend auth | 회원가입 시 영문/숫자/특수문자 포함 8자 이상 |
| `email` | backend auth | unique 이메일 |
| `displayName` | backend auth | unique 닉네임, 상단 인사 표시 |

## 기획 확인 필요

- 비밀번호 찾기/이메일 인증은 아직 범위 밖.
- 소셜 로그인은 아직 범위 밖.

## 변경 로그

- 2026-06-23: 세션 로그인 프론트 연결, 회원가입 양식 제한, 상단 로그인/로그아웃 상태 기준 추가.
- 2026-06-23: 로그인 화면에서 회원가입 폼을 분리하고 `/auth/register`, `/auth/find-account` 라우트 추가. 로그아웃 hover/focus 상태 추가.
- 2026-06-23: 로그인/회원가입/ID-PW 찾기 폼 중앙 정렬과 계정 플로우 버튼 hover/focus 기준 추가.
