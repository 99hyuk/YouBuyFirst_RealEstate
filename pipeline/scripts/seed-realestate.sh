#!/usr/bin/env bash
# 팀원이 `docker compose up`만 하면 실거래(MOLIT) 데이터가 채워지도록 하는 1회성 시드 스크립트.
# 멱등: 이미 적재돼 있으면 건너뛴다. DATA_GO_SERVICE_KEY가 없으면 안내 후 종료.
set -uo pipefail

BACKEND="${SPRING_BASE_URL:-http://backend:8080}"

# 현재 전체 범위(서울/부산/인천/대구/대전/광주/울산/경기 주요 시군구 21곳).
REGIONS="11680 11650 11710 11440 11110 11500 11350 11560 11170 26350 26500 26230 28185 27260 30200 29200 31140 41135 41117 41285 41465"
# 현재월은 전체 매물유형, 비교월은 아파트(트렌드 계산용)만 적재 → 현재 DB 범위와 동일.
ALL_DATASETS="trade rent offi-trade offi-rent rh-trade rh-rent sh-trade sh-rent silv-trade"
APT_DATASETS="trade rent"

# 오늘 기준 n개월 전의 YYYYMM (월이 바뀌어도 매번 자동 계산, 하드코딩 제거).
ym_offset() {
  python3 - "$1" <<'PY'
import sys, datetime
months_ago = int(sys.argv[1])
today = datetime.date.today()
total = today.year * 12 + (today.month - 1) - months_ago
print(f"{total // 12:04d}{total % 12 + 1:02d}")
PY
}

# 현재 기준월 + 기간 비교월(MoM/6개월/YoY) - 항상 "지금" 기준으로 자동 계산한다.
# REALESTATE_CURRENT_DEAL_YM을 명시적으로 지정하면 그 값을 그대로 쓴다(테스트/백필용 override).
CURRENT_YM="${REALESTATE_CURRENT_DEAL_YM:-$(ym_offset 0)}"
COMPARISON_YMS="$(ym_offset 1) $(ym_offset 6) $(ym_offset 12)"

# 백엔드가 응답 가능한지(urllib, curl 의존 제거).
http_ok() {
  python3 - "$1" <<'PY'
import sys, urllib.request
try:
    urllib.request.urlopen(sys.argv[1], timeout=5)
except Exception:
    sys.exit(1)
PY
}

# 실거래 데이터가 이미 있으면 0(있음), 없으면 1.
has_data() {
  python3 - "$BACKEND" <<'PY'
import sys, json, urllib.request
url = sys.argv[1] + "/api/realestate/market-facts?factType=apt_trade&limit=1"
try:
    data = json.load(urllib.request.urlopen(url, timeout=10))
    sys.exit(0 if data.get("items") else 1)
except Exception:
    sys.exit(1)
PY
}

echo "[seed] 백엔드 준비 대기: $BACKEND"
for _ in $(seq 1 60); do
  if http_ok "$BACKEND/v3/api-docs"; then echo "[seed] 백엔드 준비됨"; break; fi
  sleep 5
done

if has_data; then
  echo "[seed] 실거래 데이터가 이미 있어 시드를 건너뜁니다(멱등)."
  exit 0
fi

if [ -z "${DATA_GO_SERVICE_KEY:-}" ]; then
  echo "[seed] DATA_GO_SERVICE_KEY가 없어 MOLIT를 호출할 수 없습니다. .env에 키를 넣고 다시 실행하세요."
  exit 0
fi

echo "[seed] 실거래 데이터 시드 시작(최초 1회, 수 분 소요)..."
for code in $REGIONS; do
  youbuyfirst-pipeline realestate-market-facts-push \
    --realestate-lawd-code "$code" --realestate-deal-ym "$CURRENT_YM" \
    --realestate-datasets $ALL_DATASETS \
    || echo "[seed] 경고: $code $CURRENT_YM 실패(건너뜀)"
  for ym in $COMPARISON_YMS; do
    youbuyfirst-pipeline realestate-market-facts-push \
      --realestate-lawd-code "$code" --realestate-deal-ym "$ym" \
      --realestate-datasets $APT_DATASETS \
      || echo "[seed] 경고: $code $ym 실패(건너뜀)"
  done
  echo "[seed] 완료 $code"
done
echo "[seed] 시드 완료"
