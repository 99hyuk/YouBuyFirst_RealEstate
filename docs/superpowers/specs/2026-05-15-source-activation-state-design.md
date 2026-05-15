# 소스별 활성화 상태 설계

## 배경

너나사 (YouBuyFirst)는 커뮤니티 반응을 30분 단위로 집계하되, 모든 커뮤니티 소스를 같은 방식으로 공개 운영하지 않습니다. 기존 문서에는 `enabled`, `public-demo-only`, `local-research-only`, `disabled` 상태가 이미 정의되어 있었지만, 각 상태가 crawler, backend, data, front에서 어떤 행동을 뜻하는지는 한곳에 모여 있지 않았습니다.

이번 설계는 구현 PR이 아니라 병렬 구현을 위한 작은 계약입니다. 목표는 `crawl`, `data`, `front`, `ops` 에이전트가 같은 상태 의미를 공유하게 하는 것입니다.

## 목표

- 소스별 상태값의 의미를 실행 관점으로 명확히 합니다.
- 공개 배포 리스크와 로컬 연구/시연 편의성을 분리합니다.
- 새로운 소스는 보수적인 기본값으로 시작하게 합니다.
- `CrawlTarget`, scheduler, front 표시 정책이 같은 상태 계약을 읽게 합니다.

## 비목표

- 이번 작업에서 DB migration을 만들지 않습니다.
- 이번 작업에서 crawler parser나 scheduler 코드를 바꾸지 않습니다.
- 이번 작업에서 공개 운영 가능 여부를 법적으로 확정하지 않습니다.
- 이번 작업에서 사용자 대시보드 UI를 구현하지 않습니다.

## 상태값

| 상태 | 외부 요청 | 저장 | 공개 화면 | 용도 |
| --- | --- | --- | --- | --- |
| `enabled` | 허용 | 제한 원문 정책 안에서 허용 | 집계 지표 표시 가능 | 정책 검토가 끝난 운영 소스 |
| `public-demo-only` | 공개 환경에서는 금지 | 공개 환경에서는 fixture/sample만 사용 | demo/stale/sample 표시 가능 | 공개 시연용 대체 데이터 |
| `local-research-only` | 로컬/비공개 연구에서만 허용 | 로컬 연구 데이터만 허용 | 공개 화면 노출 금지 | 검토 전 수집 실험 |
| `disabled` | 금지 | 신규 저장 금지 | 숨김 또는 비활성 표시 | 위험, 차단, 접근 불가, 미검토 소스 |

`disabled`는 기존에 저장된 데이터를 즉시 삭제한다는 뜻이 아닙니다. 신규 수집과 신규 공개 노출을 막는 상태이며, 삭제나 보관 기간 조정은 별도 retention 정책으로 다룹니다.

## 기본값

새 소스는 기본적으로 `disabled`에서 시작합니다.

현재 MVP 소스인 네이버 종토방과 에펨코리아는 로컬 연구/시연 범위에서는 `local-research-only`로 취급할 수 있습니다. 공개 배포 환경에서는 별도 검토 전까지 `enabled`로 올리지 않습니다. 공개 화면이 필요하면 `public-demo-only` fixture 또는 샘플 집계로 대체합니다.

## 트랙별 책임

`ops`는 소스 상태 기준, 공개 배포 정책, Notion/문서 기록을 관리합니다. 상태 변경은 작업 로그에 남기고, 공개 운영 영향이 있으면 별도 검토 항목으로 둡니다.

`crawl`은 scheduler와 adapter가 상태값을 지키게 합니다. `enabled` 또는 허용된 로컬 환경의 `local-research-only`만 실제 외부 요청을 보냅니다. `public-demo-only`와 `disabled`는 외부 요청을 보내지 않습니다.

`data`는 소스 상태를 분석 품질과 지표 해석에 반영합니다. `public-demo-only` 데이터는 실제 시장 반응처럼 학습/성과 비교 근거로 과장하지 않고, `local-research-only` 데이터는 공개 지표 산식의 정본으로 쓰지 않습니다.

`front`는 상태를 사용자에게 오해 없이 보여줍니다. `public-demo-only`는 샘플/시연 데이터임을 드러내고, `local-research-only`는 공개 UI에 노출하지 않습니다. 원문 재게시와 작성자 추적은 어떤 상태에서도 하지 않습니다.

## CrawlTarget 연결

`CrawlTarget`은 종목 게시판형 소스의 우선순위를 다루는 실행 단위입니다. 소스 상태는 `CrawlTarget`보다 상위 게이트입니다.

- 소스가 `enabled`이면 target queue가 정상 작동할 수 있습니다.
- 소스가 `local-research-only`이면 로컬/비공개 실행에서만 target queue가 작동할 수 있습니다.
- 소스가 `public-demo-only`이면 target queue를 만들더라도 외부 요청 실행으로 이어지면 안 됩니다.
- 소스가 `disabled`이면 target 생성과 실행 모두 막습니다.

## 구현 순서 제안

1. `crawl` PR에서 static source policy registry를 둡니다.
2. scheduler가 source policy와 실행 환경을 보고 adapter 실행 여부를 결정합니다.
3. backend admin 조회나 Swagger에는 source 상태를 읽을 수 있는 작은 조회 경로를 추가합니다.
4. front 와이어프레임은 source 상태에 따라 `sample`, `unavailable`, `local only` 표시 후보를 mock data에 넣습니다.
5. 운영 중 상태 변경이 잦아질 때만 DB 기반 관리 화면을 검토합니다.

초기 구현은 DB보다 static config가 낫습니다. 상태 변경 빈도가 낮고, 먼저 필요한 것은 런타임 관리 화면보다 병렬 작업자들이 같은 의미를 따르는 것입니다.

## 검증 기준

- 새 소스의 기본 상태가 `disabled`인지 테스트합니다.
- 공개 환경에서 `public-demo-only`, `local-research-only`, `disabled` 소스가 외부 요청을 보내지 않는지 테스트합니다.
- `enabled`가 아니어도 기존 저장 데이터의 admin 조회가 즉시 삭제처럼 동작하지 않는지 확인합니다.
- front mock에서는 demo/sample 데이터와 실제 수집 데이터를 문구상 섞지 않습니다.
- PR 본문에는 상태별 허용 행동과 남은 공개 배포 리스크를 적습니다.

## 후속 작업

- `crawl`: source policy registry와 scheduler gate 구현
- `crawl`: `CrawlTarget` 최소 설계에서 source 상태를 상위 게이트로 반영
- `front`: source 상태가 포함된 mock data와 화면 표시 후보 정리
- `ops`: 공개 배포 전 source review checklist 추가
