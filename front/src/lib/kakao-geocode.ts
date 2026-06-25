import type { TransactionItem } from './realestate-transaction-browse';

// 단지 좌표는 백엔드(/api/realestate/geocode)에서 일괄 해석한다. 백엔드가 카카오
// 지오코딩 결과를 DB에 캐시하므로, 같은 단지는 다음부터 외부 호출 없이 즉시 반환되고
// 브라우저는 지역당 요청 1건만 보낸다.

type GeocodeResult = { query: string; lat: number; lng: number };
type Fetcher = (input: string, init?: RequestInit) => Promise<Response>;
type Coordinate = { lat: number; lng: number };

const maxGeocodeDistanceKm = 45;

function cleanQuery(value: string): string {
  return value.replace(/\s+/g, ' ').trim();
}

function compact(value: string): string {
  return value.replace(/\s+/g, '');
}

function pushQuery(queries: string[], value: string | null | undefined): void {
  const query = cleanQuery(value ?? '');
  if (query && !queries.includes(query)) {
    queries.push(query);
  }
}

function firstRegionToken(item: TransactionItem): string {
  return cleanQuery(item.gu).split(' ')[0] ?? '';
}

function blockStyleAliases(item: TransactionItem): string[] {
  const aliases: string[] = [];
  const city = firstRegionToken(item);
  const compactName = compact(item.name);
  const nameWithoutCity = city && compactName.startsWith(city)
    ? compactName.slice(city.length)
    : compactName;
  const match = nameWithoutCity.match(/^(.+?\d+지구)(.+?)(\d+)블록$/);
  if (!match) return aliases;

  const [, district, complexName, blockNumber] = match;
  const districtCore = district.replace(/\d+지구$/, '');
  const districtBlock = `${district} ${complexName} ${blockNumber}`;
  const coreBlock = `${districtCore} ${complexName} ${blockNumber}`;

  pushQuery(aliases, city ? `${city}${district}${complexName}${blockNumber}단지` : null);
  pushQuery(aliases, city ? `${city} ${districtBlock}단지` : null);
  pushQuery(aliases, `${district}${complexName}${blockNumber}단지`);
  pushQuery(aliases, `${districtBlock}단지`);
  pushQuery(aliases, `${districtCore}${complexName}${blockNumber}단지`);
  pushQuery(aliases, `${coreBlock}단지`);
  pushQuery(aliases, `${item.gu} ${districtCore} ${complexName} ${blockNumber}단지`);
  pushQuery(aliases, `${complexName}${blockNumber}단지`);
  pushQuery(aliases, `${complexName} ${blockNumber}단지`);
  pushQuery(aliases, `${complexName}${blockNumber}블록`);
  pushQuery(aliases, `${complexName} ${blockNumber}블록`);

  return aliases;
}

export function buildGeocodeQueriesForItem(item: TransactionItem): string[] {
  const queries: string[] = [];
  pushQuery(queries, `${item.gu} ${item.region} ${item.name}`);
  pushQuery(queries, `${item.gu} ${item.name}`);
  pushQuery(queries, `${item.region} ${item.name}`);
  pushQuery(queries, item.name);

  for (const alias of blockStyleAliases(item)) {
    pushQuery(queries, alias);
  }

  return queries;
}

function distanceKm(left: Coordinate, right: Coordinate): number {
  const earthRadiusKm = 6371;
  const toRad = (value: number) => value * Math.PI / 180;
  const dLat = toRad(right.lat - left.lat);
  const dLng = toRad(right.lng - left.lng);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(left.lat)) * Math.cos(toRad(right.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * earthRadiusKm * Math.asin(Math.sqrt(a));
}

function isNearExpectedRegion(item: TransactionItem, coordinate: Coordinate): boolean {
  if (!Number.isFinite(item.lat) || !Number.isFinite(item.lng)) return true;
  return distanceKm({ lat: item.lat, lng: item.lng }, coordinate) <= maxGeocodeDistanceKm;
}

function coordinateForItem(
  item: TransactionItem,
  queries: string[],
  coordinateByQuery: Map<string, Coordinate>
): Coordinate | null {
  for (const query of queries) {
    const coordinate = coordinateByQuery.get(query);
    if (coordinate && isNearExpectedRegion(item, coordinate)) {
      return coordinate;
    }
  }
  return null;
}

/**
 * 좌표를 백엔드에서 한 번에 받아 적용한다. 백엔드가 비활성이거나 실패하면 원본
 * (구 중심 좌표)을 그대로 돌려준다. 테스트 모드에서는 기본 fetch 네트워크를 타지 않는다.
 */
export async function geocodeTransactionItems(
  items: TransactionItem[],
  fetcher: Fetcher = fetch
): Promise<TransactionItem[]> {
  if (!items.length || (import.meta.env.MODE === 'test' && fetcher === fetch)) return items;

  const queriesByItem = items.map(buildGeocodeQueriesForItem);
  const queries = [...new Set(queriesByItem.flat())].filter((query) => query.length > 0);
  if (!queries.length) return items;

  const coordinateByQuery = new Map<string, Coordinate>();
  try {
    const response = await fetcher('/api/realestate/geocode', {
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

  return items.map((item, index) => {
    const coordinate = coordinateForItem(item, queriesByItem[index] ?? [], coordinateByQuery);
    return coordinate
      ? { ...item, lat: coordinate.lat, lng: coordinate.lng, coordSource: 'geocoded' as const }
      : item;
  });
}
