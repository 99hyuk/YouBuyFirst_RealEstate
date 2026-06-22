# 마이페이지 화면

## Route

- Parent: root
- Route 정보: `/realestate/mypage`
- Legacy route: `/realestate/watchlist`는 북마크 호환을 위해 `/realestate/mypage`로 redirect
- Child screens: 저장 대상 추가 drawer, 알림 조건 관리 drawer, 개인 메모 editor 후보

## 화면 목적

사용자가 저장한 지역을 관리하고, 지난 방문 이후 바뀐 시장 사실을 확인하는 개인화 공간입니다.

지역 반응 TOP10이나 임시 관심 후보를 저장 목록처럼 보여주는 화면이 아닙니다. 로그인/사용자 저장 API가 열리기 전에는 실제 저장 지역·단지처럼 보이는 mock 목록을 두지 않고, `로그인 후 확인`, `데이터 확인 전`, `준비 중` 상태를 분리해서 보여줍니다.

## 현재 섹션

- 내 부동산 관찰 보드 hero
  - 사용자 저장 기반 개인 공간임을 설명
  - 로그인 연동 전 준비 상태 표시
- 마이페이지 상태 요약
  - 저장 대상, 최근 변화, 알림 조건, 개인 메모
- 내 저장 지역·단지
  - 저장된 대상이 없을 때 빈 상태 표시
  - 태그 후보: 실거주, 전세, 청약, 투자관찰, 교통, 재건축, 공급
- 지난 방문 이후 바뀐 것
  - 새 실거래·전세 거래
  - 주요 일정 도래
  - 정책·공급·청약 이슈
  - 근거 브리핑 갱신
  - 공식 데이터 없음
- 내 알림 조건
  - 거래 변화, 전세 압력, 주요 일정, 정책·공급 이벤트
- 지역별 관찰 메모
  - 전세 위주로 보기, 청약 일정 체크, 실거주 후보 같은 개인 메모 예시
- 저장 지역 비교
  - 실거래, 전세, 공급, 일정, 근거 기준 비교 준비 상태

## 상태와 빈 화면

- loading: 저장 목록 API가 붙으면 skeleton을 보여줍니다.
- empty: 저장된 지역·단지가 없다는 빈 상태와 저장 태그 후보를 보여줍니다.
- error: 저장 목록, 알림 조건, 개인 메모 실패를 분리합니다.
- stale/mock: 사용자 저장 목록에는 mock row를 넣지 않습니다. 시장 fact 자체가 지연되면 해당 대상의 `공개 지연`, `데이터 확인 전` 상태로만 표시합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `watchSummary` | user/backend | 로그인 후 저장 대상 수, 최근 변화 수, 알림 조건 수, 메모 수 |
| `watchTargets` | user/realestate | 사용자가 저장한 지역/단지 목록과 내부 target id |
| `watchTargetChanges` | realestate/user | 지난 방문 이후 바뀐 실거래, 전세, 일정, 정책·공급 이슈 |
| `alertRules` | user/realestate | 거래 변화, 전세 압력, 일정, 정책·공급 이벤트 알림 조건 |
| `observationNotes` | user/realestate | 사용자가 직접 남긴 지역별 관찰 메모 |
| `watchComparison` | realestate/user | 저장 지역 비교용 실거래, 전세, 공급, 일정, 근거 상태 |

## 기획 확인 필요

- 로그인/사용자 저장 API를 여는 시점
- 저장 가능한 대상 범위: 지역, 동, 단지, 생활권
- 알림 조건 threshold와 notification channel
- 개인 메모를 서버 저장으로 둘지 로컬 우선으로 둘지

## 변경 로그

- 2026-06-23: 기존 watchlist 화면을 로그인 기반 `마이페이지`로 전환. `/realestate/mypage`를 정본 route로 두고 `/realestate/watchlist`는 redirect로 유지.
- 2026-06-22: 관심 후보 기준을 reaction ranking에서 지도/실거래 탐색 기반 시장 후보로 전환.
- 2026-06-15: 로그인/저장 전 mock watchlist를 제거하고 region reaction ranking 기반 관심 후보와 빈 상태로 전환.
- 2026-06-12: 화면 정본 route를 `/realestate/watchlist`로 고정하고 레거시 호환 route를 제거.
- 2026-06-01: 기존 원장형 화면을 관심 지역 관리 화면으로 전환.
