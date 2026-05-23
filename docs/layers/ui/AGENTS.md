# ui layer 작업 지침

ui layer는 화면 구조, route, Screen Brief, 디자인 시스템, fixture/API 후보, 화면 문구 표현을 소유합니다.

## 시작

- 화면 작업이면 먼저 해당 `screens/<screen>.md`를 봅니다.
- 공통 스타일, 색상, spacing, panel/data card 기준이면 `DESIGN_SYSTEM.md`를 봅니다.
- 종목 상세 검은 배너 표현이면 `STOCK_DETAIL_BANNER.md`를 봅니다.
- 전체 UI 색인이 필요할 때만 `README.md`를 봅니다.

## 경계

- UI는 도메인 contract를 임의 확정하지 않습니다. 화면 후보 필드는 Screen Brief에 남기고, 확정 contract는 해당 도메인 문서로 승격합니다.
- 새 화면/child detail이 생기면 별도 지시가 없어도 해당 Screen Brief를 갱신합니다.
- Screen Brief는 최신 기준만 유지합니다. 긴 피드백 전문, 폐기 시안, 긴 변경 이력은 누적하지 않습니다.

## 검증

- 화면/라우팅/반응형/차트 변경은 실제 브라우저 확인 가치가 있으면 Browser/gstack으로 확인합니다.
- 검증 결과는 콘솔/DOM 전문이 아니라 핵심 오류, 화면 경로, 남은 리스크로 요약합니다.
