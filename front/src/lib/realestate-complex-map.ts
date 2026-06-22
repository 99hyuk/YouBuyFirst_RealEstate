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
    ? payload.items
      .filter(isDisplayableNearbyComplex)
      .map(toComplexMapMarker)
      .filter((item): item is ComplexMapMarker => item !== null)
    : [];
}

function isDisplayableNearbyComplex(item: RealEstateNearbyComplexItem): boolean {
  const status = (item.dataStatus ?? item.coordinateStatus ?? '').toLowerCase();
  const provider = (item.provider ?? item.coordinateProvider ?? '').toLowerCase();
  return status !== 'mock' && !provider.includes('fixture');
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
    change: item.change ?? '확인 필요',
    reaction: item.reaction ?? '반응 지표 연결 전',
    provider: item.provider ?? item.coordinateProvider ?? '출처 확인 필요',
    asOf: dateOnly(item.asOf) ?? '기준일 확인 필요',
    dataStatus: displayDataStatus(item.dataStatus, item.coordinateStatus, item.stale),
    note: item.note ?? '좌표와 시장 사실 검증이 필요한 marker입니다.'
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
  const status = statusLabel(dataStatus ?? coordinateStatus);
  return stale ? `${status} · 갱신 지연` : status;
}

function statusLabel(status?: string | null): string {
  const normalized = (status ?? '').toLowerCase();
  if (normalized === 'candidate') return '좌표 후보';
  if (normalized === 'verified' || normalized === 'ok') return '검증 완료';
  if (normalized === 'partial') return '부분 반영';
  if (normalized === 'insufficient' || normalized === 'mock') return '수집 전';
  if (normalized === 'low_sample') return '표본 부족';
  if (normalized === 'empty') return '데이터 없음';
  if (normalized === 'stale') return '갱신 지연';
  return status || '확인 필요';
}

function dateOnly(value?: string | null): string | null {
  if (!value) return null;
  return value.slice(0, 10);
}
