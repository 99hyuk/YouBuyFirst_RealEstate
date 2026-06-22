import type { ComplexMapMarker, ComplexMapTone } from '../components/KakaoComplexMap.vue';
import { fetchRealEstateMarketFacts, type RealEstateMarketFact } from './realestate-market-facts';
import seed from '../fixtures/complex-browse-seed.json';

export type DealType = 'trade' | 'rent';

export type ComplexBrowseItem = {
  id: string;
  name: string;
  region: string;
  gu: string;
  dealType: DealType;
  priceLabel: string;
  priceValue: number;
  dealCount: number;
  areaLabel: string;
  builtYear: number | null;
  asOf: string;
  dataStatus: string;
  stale: boolean;
  lat: number;
  lng: number;
  tone: ComplexMapTone;
};

export type ComplexBrowseResult = {
  items: ComplexBrowseItem[];
  source: 'live' | 'fallback';
};

export type ComplexBrowseFilter = {
  dealType?: DealType | 'all';
  query?: string;
};

export type ComplexBrowseSort = 'price-desc' | 'price-asc' | 'count-desc';

type GuCentroid = { lat: number; lng: number; name: string };
const guCentroids = seed.guCentroids as Record<string, GuCentroid>;
const fallbackCentroid = seed.fallbackCentroid as GuCentroid;

const dealTypeLabels: Record<DealType, string> = {
  trade: '매매',
  rent: '전·월세'
};

export function dealTypeLabel(dealType: DealType): string {
  return dealTypeLabels[dealType];
}

/** Deterministic small offset so complexes in the same gu spread out instead of stacking. */
export function complexCoordinate(legalDongCode: string | null | undefined, key: string): { lat: number; lng: number } {
  const base = (legalDongCode && guCentroids[legalDongCode]) || fallbackCentroid;
  const hash = hashString(key);
  const latOffset = (((hash % 1000) / 1000) - 0.5) * 0.026;
  const lngOffset = ((((hash >> 10) % 1000) / 1000) - 0.5) * 0.03;
  return {
    lat: Number((base.lat + latOffset).toFixed(6)),
    lng: Number((base.lng + lngOffset).toFixed(6))
  };
}

function hashString(value: string): number {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash;
}

function dealTypeFromFactType(factType?: string): DealType | null {
  if (factType === 'apt_trade') return 'trade';
  if (factType === 'apt_rent') return 'rent';
  return null;
}

function numberValue(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function stringValue(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
}

function formatManwonAsEok(value: number): string {
  return `${(value / 10000).toLocaleString('ko-KR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}억`;
}

function tradePriceLabel(value: number): string {
  return formatManwonAsEok(value);
}

function rentPriceLabel(deposit: number, monthlyRent: number): string {
  if (monthlyRent > 0) {
    return `보증 ${formatManwonAsEok(deposit)} / 월 ${monthlyRent.toLocaleString('ko-KR')}만`;
  }
  return `전세 ${formatManwonAsEok(deposit)}`;
}

function toneFromBuiltYear(builtYear: number | null): ComplexMapTone {
  if (builtYear === null) return 'flat';
  if (builtYear >= 2015) return 'up';
  if (builtYear <= 2005) return 'down';
  return 'flat';
}

type Accumulator = {
  id: string;
  name: string;
  region: string;
  gu: string;
  dealType: DealType;
  priceValue: number;
  dealCount: number;
  minArea: number | null;
  maxArea: number | null;
  builtYear: number | null;
  deposit: number;
  monthlyRent: number;
  asOf: string | null;
  legalDongCode: string | null;
  dataStatus: string;
  stale: boolean;
};

/** Group raw market facts into one card per complex + deal type. Pure for testing. */
export function aggregateComplexes(facts: RealEstateMarketFact[]): ComplexBrowseItem[] {
  const groups = new Map<string, Accumulator>();

  for (const fact of facts) {
    const dealType = dealTypeFromFactType(fact.factType);
    if (!dealType) continue;
    const valueJson = fact.valueJson ?? {};
    const name = stringValue(valueJson.apartmentName);
    if (!name) continue;
    const region = stringValue(valueJson.legalDongName) ?? '지역 확인 필요';
    const legalDongCode = fact.legalDongCode ?? null;
    const groupKey = `${name}|${region}|${dealType}`;

    const area = numberValue(valueJson.exclusiveAreaM2);
    const builtYear = numberValue(valueJson.builtYear);
    const dealAmount = numberValue(valueJson.dealAmountManwon) ?? 0;
    const deposit = numberValue(valueJson.depositAmountManwon) ?? numberValue(valueJson.depositManwon) ?? 0;
    const monthlyRent = numberValue(valueJson.monthlyRentAmountManwon) ?? numberValue(valueJson.monthlyRentManwon) ?? 0;
    const observedAt = fact.observedAt ?? fact.asOf ?? null;

    const existing = groups.get(groupKey);
    if (!existing) {
      groups.set(groupKey, {
        id: groupKey,
        name,
        region,
        gu: (legalDongCode && guCentroids[legalDongCode]?.name) || '서울',
        dealType,
        priceValue: dealType === 'trade' ? dealAmount : deposit,
        dealCount: 1,
        minArea: area,
        maxArea: area,
        builtYear,
        deposit,
        monthlyRent,
        asOf: observedAt,
        legalDongCode,
        dataStatus: fact.dataStatus ?? 'unknown',
        stale: Boolean(fact.stale)
      });
      continue;
    }

    existing.dealCount += 1;
    if (area !== null) {
      existing.minArea = existing.minArea === null ? area : Math.min(existing.minArea, area);
      existing.maxArea = existing.maxArea === null ? area : Math.max(existing.maxArea, area);
    }
    // Keep the most recent observation as representative.
    if (observedAt && (!existing.asOf || observedAt > existing.asOf)) {
      existing.asOf = observedAt;
      existing.priceValue = dealType === 'trade' ? dealAmount : deposit;
      existing.deposit = deposit;
      existing.monthlyRent = monthlyRent;
    }
    existing.stale = existing.stale || Boolean(fact.stale);
  }

  return [...groups.values()].map((group) => {
    const coordinate = complexCoordinate(group.legalDongCode, group.id);
    return {
      id: group.id,
      name: group.name,
      region: group.region,
      gu: group.gu,
      dealType: group.dealType,
      priceLabel:
        group.dealType === 'trade'
          ? tradePriceLabel(group.priceValue)
          : rentPriceLabel(group.deposit, group.monthlyRent),
      priceValue: group.priceValue,
      dealCount: group.dealCount,
      areaLabel: areaLabel(group.minArea, group.maxArea),
      builtYear: group.builtYear,
      asOf: group.asOf ? group.asOf.slice(0, 10) : 'asOf 확인 필요',
      dataStatus: group.dataStatus,
      stale: group.stale,
      lat: coordinate.lat,
      lng: coordinate.lng,
      tone: toneFromBuiltYear(group.builtYear)
    } satisfies ComplexBrowseItem;
  });
}

function areaLabel(minArea: number | null, maxArea: number | null): string {
  if (minArea === null || maxArea === null) return '면적 확인 필요';
  if (Math.abs(minArea - maxArea) < 0.5) return `전용 ${minArea.toFixed(0)}㎡`;
  return `전용 ${minArea.toFixed(0)}~${maxArea.toFixed(0)}㎡`;
}

/** Filter + sort the aggregated cards. Pure for testing. */
export function filterComplexes(
  items: ComplexBrowseItem[],
  filter: ComplexBrowseFilter = {},
  sort: ComplexBrowseSort = 'price-desc'
): ComplexBrowseItem[] {
  const query = (filter.query ?? '').trim().toLowerCase();
  const dealType = filter.dealType ?? 'all';

  const filtered = items.filter((item) => {
    if (dealType !== 'all' && item.dealType !== dealType) return false;
    if (query && !`${item.name} ${item.region} ${item.gu}`.toLowerCase().includes(query)) return false;
    return true;
  });

  return filtered.sort((left, right) => {
    if (sort === 'count-desc') return right.dealCount - left.dealCount;
    if (sort === 'price-asc') return left.priceValue - right.priceValue;
    return right.priceValue - left.priceValue;
  });
}

export function toComplexMarkers(items: ComplexBrowseItem[]): ComplexMapMarker[] {
  return items.map((item) => ({
    targetId: item.id,
    name: item.name,
    address: `${item.gu} ${item.region}`,
    region: item.region,
    lat: item.lat,
    lng: item.lng,
    tone: item.tone,
    price: item.priceLabel,
    change: `${dealTypeLabels[item.dealType]} ${item.dealCount}건`,
    reaction: item.builtYear ? `${item.builtYear}년 준공` : '준공연도 확인 필요',
    provider: 'molit',
    asOf: item.asOf,
    dataStatus: item.stale ? `${item.dataStatus} · stale` : item.dataStatus,
    note: '구 중심 좌표 기준 배치 · 단지 정밀 좌표 매핑 전'
  }));
}

function mockComplexItems(): ComplexBrowseItem[] {
  const mocks = seed.mockComplexes as Array<{
    id: string;
    name: string;
    region: string;
    gu: string;
    dealType: DealType;
    priceValue: number;
    dealCount: number;
    areaLabel: string;
    builtYear: number;
    lat: number;
    lng: number;
    tone: ComplexMapTone;
  }>;

  return mocks.map((mock) => ({
    id: mock.id,
    name: mock.name,
    region: mock.region,
    gu: mock.gu,
    dealType: mock.dealType,
    priceLabel:
      mock.dealType === 'trade'
        ? tradePriceLabel(mock.priceValue)
        : rentPriceLabel(mock.priceValue, 0),
    priceValue: mock.priceValue,
    dealCount: mock.dealCount,
    areaLabel: mock.areaLabel,
    builtYear: mock.builtYear,
    asOf: 'mock',
    dataStatus: 'mock',
    stale: true,
    lat: mock.lat,
    lng: mock.lng,
    tone: mock.tone
  }));
}

type Fetcher = (input: string) => Promise<Response>;

export async function fetchComplexBrowse(fetcher: Fetcher = fetch): Promise<ComplexBrowseResult> {
  try {
    const facts = await fetchRealEstateMarketFacts({}, fetcher);
    const items = aggregateComplexes(facts);
    if (items.length) {
      return { items, source: 'live' };
    }
  } catch {
    // fall through to mock fallback
  }
  return { items: mockComplexItems(), source: 'fallback' };
}
