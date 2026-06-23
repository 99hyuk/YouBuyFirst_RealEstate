import type { TransactionItem } from './realestate-transaction-browse';

// 단지 좌표는 백엔드(/api/realestate/geocode)에서 일괄 해석한다. 백엔드가 카카오
// 지오코딩 결과를 DB에 캐시하므로, 같은 단지는 다음부터 외부 호출 없이 즉시 반환되고
// 브라우저는 지역당 요청 1건만 보낸다(예전엔 단지마다 1건씩 보냈음).

type GeocodeResult = { query: string; lat: number; lng: number };

function geocodeQuery(item: TransactionItem): string {
  return `${item.gu} ${item.region} ${item.name}`.replace(/\s+/g, ' ').trim();
}

/**
 * 좌표를 백엔드에서 한 번에 받아 적용한다. 백엔드가 비활성이거나 실패하면 원본
 * (구 중심 좌표)을 그대로 돌려준다. 테스트 모드에서는 네트워크를 타지 않는다.
 */
export async function geocodeTransactionItems(items: TransactionItem[]): Promise<TransactionItem[]> {
  if (!items.length || import.meta.env.MODE === 'test') return items;

  const queries = [...new Set(items.map(geocodeQuery))].filter((query) => query.length > 0);
  if (!queries.length) return items;

  const coordinateByQuery = new Map<string, { lat: number; lng: number }>();
  try {
    const response = await fetch('/api/realestate/geocode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ queries })
    });
    if (!response.ok) return items;
    const payload = (await response.json()) as { results?: GeocodeResult[] };
    for (const result of payload.results ?? []) {
      if (Number.isFinite(result.lat) && Number.isFinite(result.lng)) {
        coordinateByQuery.set(result.query, { lat: result.lat, lng: result.lng });
      }
    }
  } catch {
    return items;
  }

  if (!coordinateByQuery.size) return items;

  return items.map((item) => {
    const coordinate = coordinateByQuery.get(geocodeQuery(item));
    return coordinate
      ? { ...item, lat: coordinate.lat, lng: coordinate.lng, coordSource: 'geocoded' as const }
      : item;
  });
}
