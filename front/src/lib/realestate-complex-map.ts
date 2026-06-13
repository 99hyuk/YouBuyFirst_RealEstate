import type { ComplexMapMarker, ComplexMapTone } from '../components/KakaoComplexMap.vue';

export type RealEstateNearbyComplexItem = {
  targetId: string;
  name: string;
  address?: string | null;
  region?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  tone?: ComplexMapTone | string | null;
  price?: string | null;
  change?: string | null;
  reaction?: string | null;
  provider?: string | null;
  asOf?: string | null;
  dataStatus?: string | null;
  stale?: boolean | null;
  note?: string | null;
  legalDongCode?: string | null;
  coordinateProvider?: string | null;
  coordinateStatus?: string | null;
};

export type FetchNearbyComplexParams = {
  limit?: number;
};

type Fetcher = (input: string) => Promise<Response>;

export async function fetchRealEstateNearbyComplexes(
  targetId: string,
  params: FetchNearbyComplexParams = {},
  fetcher: Fetcher = fetch
): Promise<ComplexMapMarker[]> {
  const query = new URLSearchParams();
  query.set('limit', String(params.limit ?? 20));

  const response = await fetcher(
    `/api/realestate/targets/${encodeURIComponent(targetId)}/nearby-complexes?${query.toString()}`
  );
  if (!response.ok) {
    throw new Error(`real-estate nearby complex request failed: ${response.status}`);
  }

  const payload = await response.json() as { items?: RealEstateNearbyComplexItem[] };
  return Array.isArray(payload.items)
    ? payload.items.map(toComplexMapMarker).filter((item): item is ComplexMapMarker => item !== null)
    : [];
}

function toComplexMapMarker(item: RealEstateNearbyComplexItem): ComplexMapMarker | null {
  if (!item.targetId || !item.name || !Number.isFinite(item.latitude) || !Number.isFinite(item.longitude)) {
    return null;
  }

  return {
    targetId: item.targetId,
    name: item.name,
    address: item.address ?? '주소 확인 필요',
    region: item.region ?? '지역 확인 필요',
    lat: Number(item.latitude),
    lng: Number(item.longitude),
    tone: normalizeTone(item.tone),
    price: item.price ?? '확인 필요',
    change: item.change ?? 'unknown',
    reaction: item.reaction ?? '반응 지표 연결 전',
    provider: item.provider ?? item.coordinateProvider ?? 'unknown',
    asOf: dateOnly(item.asOf) ?? 'asOf 확인 필요',
    dataStatus: displayDataStatus(item.dataStatus, item.coordinateStatus, item.stale),
    note: item.note ?? '좌표와 시장 fact 검증이 필요한 marker입니다.'
  };
}

function normalizeTone(value?: string | null): ComplexMapTone {
  if (value === 'up' || value === 'down' || value === 'flat') {
    return value;
  }
  return 'flat';
}

function displayDataStatus(
  dataStatus?: string | null,
  coordinateStatus?: string | null,
  stale?: boolean | null
): string {
  const status = dataStatus ?? coordinateStatus ?? 'unknown';
  return stale ? `${status} · stale` : status;
}

function dateOnly(value?: string | null): string | null {
  if (!value) return null;
  return value.slice(0, 10);
}
