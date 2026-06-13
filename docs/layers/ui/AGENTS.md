# ui layer 작업 지침

ui layer는 화면 구조, route, Screen Brief, 디자인 시스템, fixture/API 후보, 화면 문구 표현을 소유합니다.

## 시작

- 화면 작업이면 `WIREFRAME_HANDOFF.md`에서 현재 UI 방향을 짧게 확인한 뒤, 해당 `screens/<screen>.md`를 봅니다.
- 공통 스타일, 색상, spacing, panel/data card 기준이면 `DESIGN_SYSTEM.md`를 봅니다.
- 지역/단지 상세 평가 표현이면 `screens/realestate-target-detail.md`를 봅니다.
- 전체 UI 색인이 필요할 때만 `README.md`를 봅니다.

## 기획 이해 게이트

- ui 작업자는 화면을 단순 구현물로 보지 않고, 사용자가 이 화면에서 무엇을 판단하는지 이해한 뒤 수정합니다.
- 기본 입력은 `WIREFRAME_HANDOFF.md`와 해당 Screen Brief입니다. 제품 전체 방향이 흔들릴 때만 `docs/product/FINAL_PRODUCT_PLAN.md`의 관련 섹션을 `rg`로 좁혀 봅니다.
- API 후보, 지표 정의, market fact provider, 에이전트 평가처럼 도메인 contract가 필요한 경우 해당 도메인 문서를 전문 읽지 말고 Screen Brief의 `API 후보`와 담당 도메인 `AGENTS.md`/`README.md`의 관련 섹션만 확인합니다.
- archive, visual history, 긴 피드백 전문은 현재 Screen Brief가 부족하거나 사용자가 특정 과거 화면을 지목한 경우에만 검색합니다.

## 경계

- UI는 도메인 contract를 임의 확정하지 않습니다. 화면 후보 필드는 Screen Brief에 남기고, 확정 contract는 해당 도메인 문서로 승격합니다.
- 새 화면/child detail이 생기면 별도 지시가 없어도 해당 Screen Brief를 갱신합니다.
- Screen Brief는 최신 기준만 유지합니다. 긴 피드백 전문, 폐기 시안, 긴 변경 이력은 누적하지 않습니다.
- 삭제된 레거시 화면 문서는 새 작업의 정본으로 삼지 않습니다.

## 검증

- 화면/라우팅/반응형/차트 변경은 실제 브라우저 확인 가치가 있으면 Browser/gstack으로 확인합니다.
- 검증 결과는 콘솔/DOM 전문이 아니라 핵심 오류, 화면 경로, 남은 리스크로 요약합니다.
