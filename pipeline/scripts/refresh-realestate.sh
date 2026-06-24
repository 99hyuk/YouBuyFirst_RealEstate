#!/usr/bin/env bash
# 실거래(MOLIT) "현재월" 데이터를 주기적으로 재수집한다(지각 신고분 반영).
# MOLIT는 월 단위 발행 + 최근 달 지각신고가 늘어나므로 하루 1회면 충분하다.
# 과거(비교) 월은 사실상 고정이라 갱신하지 않는다. upsert라 중복 적재 안전.
set -uo pipefail

BACKEND="${SPRING_BASE_URL:-http://backend:8080}"
INTERVAL_MIN="${REALESTATE_REFRESH_INTERVAL_MINUTES:-1440}"   # 기본 하루 1회
CURRENT_YM="${REALESTATE_CURRENT_DEAL_YM:-202605}"
REGIONS="11680 11650 11710 11440 11110 11500 11350 11560 11170 26350 26500 26230 28185 27260 30200 29200 31140 41135 41117 41285 41465"
ALL_DATASETS="trade rent offi-trade offi-rent rh-trade rh-rent sh-trade sh-rent silv-trade"

http_ok() {
  python3 - "$1" <<'PY'
import sys, urllib.request
try:
    urllib.request.urlopen(sys.argv[1], timeout=5)
except Exception:
    sys.exit(1)
PY
}

if [ -z "${DATA_GO_SERVICE_KEY:-}" ]; then
  echo "[refresh] DATA_GO_SERVICE_KEY 없음 — 실거래 자동 갱신 비활성(대기만)."
  sleep infinity
fi

echo "[refresh] 실거래 일일 갱신 시작: 현재월=$CURRENT_YM, 간격=${INTERVAL_MIN}분"
# 초기 적재는 realestate-seed가 담당하므로, 첫 갱신은 한 주기 뒤부터.
while true; do
  sleep "$((INTERVAL_MIN * 60))"
  if ! http_ok "$BACKEND/v3/api-docs"; then
    echo "[refresh] 백엔드 미응답 — 이번 주기 건너뜀"
    continue
  fi
  echo "[refresh] 현재월($CURRENT_YM) 재수집 시작"
  for code in $REGIONS; do
    youbuyfirst-pipeline realestate-market-facts-push \
      --realestate-lawd-code "$code" --realestate-deal-ym "$CURRENT_YM" \
      --realestate-datasets $ALL_DATASETS \
      || echo "[refresh] 경고: $code 실패(건너뜀)"
  done
  echo "[refresh] 재수집 완료"
done
