# SSAFY HOME SQL 기반 부동산 DB bootstrap

확인일: 2026-06-16

## 결론

`SSAFY_HOME_Schema.sql` / `SSAFY_HOME_Dump_2604.sql`은 부동산 서비스의 실제 단지/좌표/실거래 초기 DB로 쓰기에 적합하다. 다만 운영 서비스가 `ssafy_home` 원본 테이블을 직접 읽게 만들지는 않는다.

구조는 다음처럼 둔다.

```text
SSAFY HOME SQL dump
-> ssafy_home source schema
-> tools/realestate/ssafy_home_bootstrap.sql
-> real_estate_regions
-> real_estate_targets
-> real_estate_complexes
-> real_estate_complex_provider_keys
-> real_estate_aliases
-> real_estate_target_edges
-> real_estate_market_facts
-> dashboard / map / reactions / target detail / AI evidence
```

즉 DB를 중복 운영하는 것이 아니라, 원본 dump는 재현 가능한 source/staging layer로 두고 실제 서비스 정본은 `real_estate_*` 테이블 하나로 맞춘다.

## 확인한 원본 테이블

| 원본 테이블 | 주요 필드 | 우리 서비스 매핑 |
| --- | --- | --- |
| `dongcodes` | `dong_code`, `sido_name`, `gugun_name`, `dong_name` | `real_estate_regions`, 지역 target, 상위/하위 지역 관계 |
| `houseinfos` | `apt_seq`, `sgg_cd`, `umd_cd`, `apt_nm`, `build_year`, `latitude`, `longitude` | 단지 target, 단지 상세, provider key, alias, 지도 marker |
| `housedeals` | `no`, `apt_seq`, `deal_year/month/day`, `exclu_use_ar`, `deal_amount` | `real_estate_market_facts`의 `apt_trade` fact |

`houseinfos.apt_seq`는 단지 외부키로 보존한다. `housedeals.apt_seq`는 이 키를 통해 단지 target과 연결한다.

## 로컬 실행 순서

현재 docker compose 기준 MySQL 컨테이너 이름은 보통 `youbuyfirst_realestate-mysql-1`이고, 서비스 DB는 `youbuyfirst`다.

```powershell
docker cp C:\Users\JYH\Downloads\SSAFY_HOME_Schema.sql youbuyfirst_realestate-mysql-1:/tmp/SSAFY_HOME_Schema.sql
docker cp C:\Users\JYH\Downloads\SSAFY_HOME_Dump_2604.sql youbuyfirst_realestate-mysql-1:/tmp/SSAFY_HOME_Dump_2604.sql
docker cp tools\realestate\ssafy_home_bootstrap.sql youbuyfirst_realestate-mysql-1:/tmp/ssafy_home_bootstrap.sql
docker cp tools\realestate\ssafy_home_housedeals_chunk.sql youbuyfirst_realestate-mysql-1:/tmp/ssafy_home_housedeals_chunk.sql

docker exec youbuyfirst_realestate-mysql-1 sh -lc "mysql --default-character-set=utf8mb4 -uroot -proot < /tmp/SSAFY_HOME_Schema.sql"
docker exec youbuyfirst_realestate-mysql-1 sh -lc "mysql --default-character-set=utf8mb4 -uroot -proot ssafy_home < /tmp/SSAFY_HOME_Dump_2604.sql"
docker exec youbuyfirst_realestate-mysql-1 sh -lc "mysql --default-character-set=utf8mb4 -uroot -proot youbuyfirst < /tmp/ssafy_home_bootstrap.sql"
```

`ssafy_home_bootstrap.sql`은 기본적으로 지역/단지/좌표/alias/provider key를 먼저 채운다. 대량 거래 이력은 chunk 전용 SQL로 나눠 실행한다.

```powershell
docker exec youbuyfirst_realestate-mysql-1 sh -lc "mysql --default-character-set=utf8mb4 -uroot -proot youbuyfirst --init-command='SET @deal_min_no=1; SET @deal_max_no=100000' < /tmp/ssafy_home_housedeals_chunk.sql"
docker exec youbuyfirst_realestate-mysql-1 sh -lc "mysql --default-character-set=utf8mb4 -uroot -proot youbuyfirst --init-command='SET @deal_min_no=100001; SET @deal_max_no=200000' < /tmp/ssafy_home_housedeals_chunk.sql"
```

전체 거래 이력을 한 번에 밀어 넣어야 할 때만 아래처럼 명시적으로 켠다. 로컬 검증에서는 chunk 방식이 더 안전하다.

```powershell
docker exec youbuyfirst_realestate-mysql-1 sh -lc "mysql --default-character-set=utf8mb4 -uroot -proot youbuyfirst --init-command='SET @import_ssafy_housedeals=TRUE' < /tmp/ssafy_home_bootstrap.sql"
```

## 검증 쿼리

```powershell
docker exec youbuyfirst_realestate-mysql-1 mysql --default-character-set=utf8mb4 -uroot -proot -e "SELECT COUNT(*) FROM ssafy_home.houseinfos; SELECT COUNT(*) FROM ssafy_home.housedeals;"
docker exec youbuyfirst_realestate-mysql-1 mysql --default-character-set=utf8mb4 -uroot -proot youbuyfirst -e "SELECT COUNT(*) FROM real_estate_complexes WHERE source='ssafy_home:houseinfos'; SELECT COUNT(*) FROM real_estate_market_facts WHERE provider='ssafy_home';"
```

서비스 API 확인:

```powershell
curl http://localhost:8080/api/realestate/market-facts?factType=apt_trade^&limit=5
curl http://localhost:8080/api/realestate/targets/search?q=래미안^&limit=5
curl http://localhost:8080/api/realestate/targets/region-seoul-mapo/nearby-complexes?limit=5
curl http://localhost:8080/api/realestate/targets/complex-ssafy-home-11440-4/market-facts?limit=1
```

2026-06-17 기준으로 위 검색/마커/단지 실거래 API는 Vite proxy(`http://127.0.0.1:5173/api/...`)에서도 같은 응답을 반환한다.

## 중복에 대한 기준

- `ssafy_home.*`는 원본 보관/재백필용이다.
- `real_estate_*`는 서비스 정본이다.
- 프론트, 크롤링 matcher, SerpApi, AI 평가 로그는 `real_estate_*`의 `targetId`만 사용한다.
- 배포/발표 환경에서 용량이 부담되면 `ssafy_home` source schema는 제외하고 `real_estate_*` 정규화 결과만 유지할 수 있다.
- 기존 mock/candidate 단지와 같은 실제 단지가 중복될 수 있다. 이 경우 `real_estate_complex_provider_keys`의 `apt_seq`와 alias/주소/좌표를 기준으로 후속 merge 작업을 진행한다.

## 남은 작업

- `real_estate_complex_provider_keys`를 조회/운영할 backend API가 아직 없으므로, 현재는 SQL bootstrap에서 직접 채운다.
- 기존 시연용 candidate 단지와 SSAFY HOME 정본 단지의 merge 규칙이 필요하다.
- 전월세 이력은 이 dump에 없으므로 공공데이터 API의 `molit_apt_rent` 백필과 함께 채워야 한다.
- `housedeals` 기반 지역별 상승/하락률 materialized summary를 만들어 지도 색상 API에 연결해야 한다.
