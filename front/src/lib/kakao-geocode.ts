import { isKakaoMapEnabled, kakaoJsKey, loadKakaoSdk } from './kakao-sdk';
import type { TransactionItem } from './realestate-transaction-browse';

// Resolve real complex coordinates via Kakao keyword place search so markers land
// on the actual building instead of a gu-centroid approximation.

const coordinateCache = new Map<string, { lat: number; lng: number }>();
const MAX_GEOCODE_PER_PASS = 160;

function geocodeQuery(item: TransactionItem): string {
  return `${item.gu} ${item.region} ${item.name}`.replace(/\s+/g, ' ').trim();
}

function searchOne(query: string): Promise<{ lat: number; lng: number } | null> {
  const globalWindow = window as any;
  const services = globalWindow.kakao?.maps?.services;
  if (!services) return Promise.resolve(null);

  return new Promise((resolve) => {
    const places = new services.Places();
    places.keywordSearch(query, (data: any[], status: string) => {
      if (status === services.Status.OK && Array.isArray(data) && data.length) {
        const lat = Number(data[0].y);
        const lng = Number(data[0].x);
        resolve(Number.isFinite(lat) && Number.isFinite(lng) ? { lat, lng } : null);
        return;
      }
      resolve(null);
    });
  });
}

/**
 * Returns a new list with coordinates replaced by Kakao place-search results where
 * available. Falls back to the original (gu-centroid) coordinates when Kakao is
 * disabled, the SDK fails to load, or a complex can't be resolved.
 */
export async function geocodeTransactionItems(items: TransactionItem[]): Promise<TransactionItem[]> {
  if (!isKakaoMapEnabled() || !kakaoJsKey() || !items.length) return items;

  try {
    await loadKakaoSdk(kakaoJsKey());
  } catch {
    return items;
  }
  if (!(window as any).kakao?.maps?.services) return items;

  const result = [...items];
  // Cap how many complexes we geocode so a large region resolves quickly; the rest
  // keep their gu-centroid placement. Cached lookups still apply on later passes.
  const geocodeLimit = Math.min(result.length, MAX_GEOCODE_PER_PASS);
  const concurrency = Math.min(6, geocodeLimit);
  let cursor = 0;

  const worker = async () => {
    while (cursor < geocodeLimit) {
      const index = cursor;
      cursor += 1;
      const item = result[index];
      const query = geocodeQuery(item);

      const cached = coordinateCache.get(query);
      if (cached) {
        result[index] = { ...item, lat: cached.lat, lng: cached.lng, coordSource: 'geocoded' };
        continue;
      }

      const coordinate = await searchOne(query).catch(() => null);
      if (coordinate) {
        coordinateCache.set(query, coordinate);
        result[index] = { ...item, lat: coordinate.lat, lng: coordinate.lng, coordSource: 'geocoded' };
      }
    }
  };

  await Promise.all(Array.from({ length: concurrency }, () => worker()));
  return result;
}
