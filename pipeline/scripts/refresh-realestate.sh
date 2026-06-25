#!/usr/bin/env bash
# 실거래(MOLIT) "현재월" 데이터를 주기적으로 재수집한다(지각 신고분 반영).
# MOLIT는 월 단위 발행 + 최근 달 지각신고가 늘어나므로 하루 1회면 충분하다.
# 비교월(MoM/6개월/YoY)은 거래 자체가 고정이라 매번 다시 받을 필요는 없지만,
# 달이 바뀌면 비교 대상 자체가 바뀌므로(예: 7월엔 6개월전이 1월→2월로 이동) 매 주기
# 빠진 비교월만 자동으로 백필한다. 이미 있는 (지역, 연월) 조합은 건드리지 않는다.
set -uo pipefail

BACKEND="${SPRING_BASE_URL:-http://backend:8080}"
INTERVAL_MIN="${REALESTATE_REFRESH_INTERVAL_MINUTES:-1440}"   # 기본 하루 1회
REGIONS="11680 11650 11710 11440 11110 11500 11350 11560 11170 26350 26500 26230 28185 27260 30200 29200 31140 41135 41117 41285 41465"
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

http_ok() {
  python3 - "$1" <<'PY'
import sys, urllib.request
try:
    urllib.request.urlopen(sys.argv[1], timeout=5)
except Exception:
    sys.exit(1)
PY
}

# 특정 지역 x 연월 조합이 이미 적재돼 있으면 0(있음), 없으면 1.
region_ym_has_data() {
  python3 - "$BACKEND" "$1" "$2" <<'PY'
import sys, json, urllib.request
base, code, ym = sys.argv[1], sys.argv[2], sys.argv[3]
url = f"{base}/api/realestate/market-facts?factType=apt_trade&legalDongCode={code}&dealYm={ym}&limit=1"
try:
    data = json.load(urllib.request.urlopen(url, timeout=10))
    sys.exit(0 if data.get("items") else 1)
except Exception:
    sys.exit(1)
PY
}

# 새 매물이 들어와도 신규 건물만 골라 카카오에 질의하도록(이미 캐시된 건물은 백엔드가
# 자동으로 건너뜀) 사전 적재를 다시 트리거한다. 백엔드가 비동기로 처리하므로 짧은
# 타임아웃으로 호출만 하고 응답은 기다리지 않는다 - 실패해도 다음 주기에 다시 시도됨.
trigger_geocode_preload() {
  python3 - "$BACKEND" <<'PY'
import sys, urllib.request
try:
    urllib.request.urlopen(urllib.request.Request(sys.argv[1] + "/api/realestate/geocode/preload", method="POST"), timeout=5)
except Exception:
    pass
PY
  echo "[refresh] 지오코딩 사전 적재 트리거 호출(신규 건물만 추가 적재, 백엔드에서 비동기 처리)"
}

backfill_comparison_months() {
  local comparison_yms="$(ym_offset 1) $(ym_offset 6) $(ym_offset 12)"
  echo "[refresh] 비교월($comparison_yms) 백필 확인"
  for ym in $comparison_yms; do
    for code in $REGIONS; do
      if region_ym_has_data "$code" "$ym"; then
        continue
      fi
      echo "[refresh] 백필: $code $ym"
      youbuyfirst-pipeline realestate-market-facts-push \
        --realestate-lawd-code "$code" --realestate-deal-ym "$ym" \
        --realestate-datasets $APT_DATASETS \
        || echo "[refresh] 경고: $code $ym 백필 실패(건너뜀)"
    done
  done
  echo "[refresh] 비교월 백필 확인 완료"
}

if [ -z "${DATA_GO_SERVICE_KEY:-}" ]; then
  echo "[refresh] DATA_GO_SERVICE_KEY 없음 — 실거래 자동 갱신 비활성(대기만)."
  sleep infinity
fi

echo "[refresh] 실거래 일일 갱신 시작: 간격=${INTERVAL_MIN}분"
# 비교월 백필은 누락분을 채우는 멱등 작업이라, 컨테이너 기동/재시작 시 한 주기를
# 기다리지 않고 즉시 한 번 확인한다(팀원 로컬처럼 비교월이 비어있는 경우 바로 복구).
if http_ok "$BACKEND/v3/api-docs"; then
  backfill_comparison_months
else
  echo "[refresh] 백엔드 미응답 — 시작 시 백필 확인 건너뜀(다음 주기에 재시도)"
fi

# 현재월 전체 데이터셋 재수집은 초기 적재(realestate-seed)와 중복되지 않도록 한 주기 뒤부터.
while true; do
  sleep "$((INTERVAL_MIN * 60))"
  if ! http_ok "$BACKEND/v3/api-docs"; then
    echo "[refresh] 백엔드 미응답 — 이번 주기 건너뜀"
    continue
  fi

  CURRENT_YM="${REALESTATE_CURRENT_DEAL_YM:-$(ym_offset 0)}"
  echo "[refresh] 현재월($CURRENT_YM) 재수집 시작"
  for code in $REGIONS; do
    youbuyfirst-pipeline realestate-market-facts-push \
      --realestate-lawd-code "$code" --realestate-deal-ym "$CURRENT_YM" \
      --realestate-datasets $ALL_DATASETS \
      || echo "[refresh] 경고: $code 실패(건너뜀)"
  done
  echo "[refresh] 현재월 재수집 완료"

  trigger_geocode_preload
  backfill_comparison_months
done
