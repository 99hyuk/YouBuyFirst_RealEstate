import type { TransactionMapMarker, TransactionMapTone } from '../components/RealEstateTransactionMap.vue';
import { fetchRealEstateMarketFacts, type RealEstateMarketFact } from './realestate-market-facts';
import seed from '../fixtures/transaction-browse-seed.json';

export type DealType = 'trade' | 'rent';
export type PropertyType = 'apt' | 'offi' | 'rh' | 'silv' | 'sh';

export type TransactionItem = {
  id: string;
  name: string;
  region: string;
  gu: string;
  propertyType: PropertyType;
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
  tone: TransactionMapTone;
  coordSource?: 'approx' | 'geocoded';
};

export type TransactionResult = {
  items: TransactionItem[];
  source: 'live' | 'fallback';
};

export type TransactionFilter = {
  propertyType?: PropertyType | 'all';
  dealType?: DealType | 'all';
  query?: string;
};

export type TransactionSort = 'price-desc' | 'price-asc' | 'count-desc';

type GuCentroid = { lat: number; lng: number; name: string };
const guCentroids = seed.guCentroids as Record<string, GuCentroid>;
const fallbackCentroid = seed.fallbackCentroid as GuCentroid;

const dealTypeLabels: Record<DealType, string> = {
  trade: '매매',
  rent: '전·월세'
};

const propertyTypeLabels: Record<PropertyType, string> = {
  apt: '아파트',
  offi: '오피스텔',
  rh: '연립·다세대',
  silv: '분양권',
  sh: '단독·다가구'
};

// 매물유형 → 백엔드 factType. 카테고리 선택 시 해당 factType만 받아와 소수 유형이 누락되지 않게 한다.
export const propertyFactTypes: Record<PropertyType, string[]> = {
  apt: ['apt_trade', 'apt_rent'],
  offi: ['offi_trade', 'offi_rent'],
  rh: ['rh_trade', 'rh_rent'],
  silv: ['silv_trade'],
  sh: ['sh_trade', 'sh_rent']
};

export function dealTypeLabel(dealType: DealType): string {
  return dealTypeLabels[dealType];
}

export function propertyTypeLabel(propertyType: PropertyType): string {
  return propertyTypeLabels[propertyType];
}

/** Deterministic small offset so complexes in the same gu spread out instead of stacking. */
export function transactionCoordinate(legalDongCode: string | null | undefined, key: string): { lat: number; lng: number } {
  const base = (legalDongCode && guCentroids[legalDongCode]) || fallbackCentroid;
  const hash = hashString(key);
  const latOffset = (((hash % 1000) / 1000) - 0.5) * 0.026;
  const lngOffset = ((((hash >> 10) % 1000) / 1000) - 0.5) * 0.03;
  return {
    lat: Number((base.lat + latOffset).toFixed(6)),
    lng: Number((base.lng + lngOffset).toFixed(6))
  };
}

export function regionCentroid(legalDongCode: string): { lat: number; lng: number } | null {
  const centroid = guCentroids[legalDongCode];
  return centroid ? { lat: centroid.lat, lng: centroid.lng } : null;
}

function hashString(value: string): number {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash;
}

function factTypeInfo(factType?: string): { propertyType: PropertyType; dealType: DealType } | null {
  if (factType === 'apt_trade') return { propertyType: 'apt', dealType: 'trade' };
  if (factType === 'apt_rent') return { propertyType: 'apt', dealType: 'rent' };
  if (factType === 'offi_trade') return { propertyType: 'offi', dealType: 'trade' };
  if (factType === 'offi_rent') return { propertyType: 'offi', dealType: 'rent' };
  if (factType === 'rh_trade') return { propertyType: 'rh', dealType: 'trade' };
  if (factType === 'rh_rent') return { propertyType: 'rh', dealType: 'rent' };
  if (factType === 'silv_trade') return { propertyType: 'silv', dealType: 'trade' };
  if (factType === 'sh_trade') return { propertyType: 'sh', dealType: 'trade' };
  if (factType === 'sh_rent') return { propertyType: 'sh', dealType: 'rent' };
  return null;
}

function numberValue(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function stringValue(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
}

// 단지명이 없는 실거래(단독·다가구 등)의 표시 라벨: 지번 주소 > 동+주택유형 > 동.
function addressLabel(valueJson: Record<string, unknown>, region: string): string | null {
  const jibun = stringValue(valueJson.jibun);
  if (jibun) return `${region} ${jibun}`;
  const raw = (valueJson.raw ?? {}) as Record<string, unknown>;
  const houseType = stringValue(valueJson.houseType) ?? stringValue(raw.houseType);
  if (houseType) return `${region} ${houseType}`;
  return region === '지역 확인 필요' ? null : region;
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

function toneFromBuiltYear(builtYear: number | null): TransactionMapTone {
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
  propertyType: PropertyType;
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
export function aggregateTransactions(facts: RealEstateMarketFact[]): TransactionItem[] {
  const groups = new Map<string, Accumulator>();

  for (const fact of facts) {
    const info = factTypeInfo(fact.factType);
    if (!info) continue;
    const { propertyType, dealType } = info;
    const valueJson = fact.valueJson ?? {};
    const region = stringValue(valueJson.legalDongName) ?? '지역 확인 필요';
    // 단지명이 없으면(단독·다가구 등) 주소(지번) 또는 동+유형으로 라벨링한다.
    const name = stringValue(valueJson.apartmentName) ?? addressLabel(valueJson, region);
    if (!name) continue;
    const legalDongCode = fact.legalDongCode ?? null;
    const groupKey = `${propertyType}|${name}|${region}|${dealType}`;

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
        propertyType,
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
    const coordinate = transactionCoordinate(group.legalDongCode, group.id);
    return {
      id: group.id,
      name: group.name,
      region: group.region,
      gu: group.gu,
      propertyType: group.propertyType,
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
      tone: toneFromBuiltYear(group.builtYear),
      coordSource: 'approx'
    } satisfies TransactionItem;
  });
}

function areaLabel(minArea: number | null, maxArea: number | null): string {
  if (minArea === null || maxArea === null) return '면적 확인 필요';
  if (Math.abs(minArea - maxArea) < 0.5) return `전용 ${minArea.toFixed(0)}㎡`;
  return `전용 ${minArea.toFixed(0)}~${maxArea.toFixed(0)}㎡`;
}

/** Filter + sort the aggregated cards. Pure for testing. */
export function filterTransactions(
  items: TransactionItem[],
  filter: TransactionFilter = {},
  sort: TransactionSort = 'price-desc'
): TransactionItem[] {
  const query = (filter.query ?? '').trim().toLowerCase();
  const dealType = filter.dealType ?? 'all';
  const propertyType = filter.propertyType ?? 'all';

  const filtered = items.filter((item) => {
    if (propertyType !== 'all' && item.propertyType !== propertyType) return false;
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

export function toTransactionMarkers(items: TransactionItem[]): TransactionMapMarker[] {
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
    note: item.coordSource === 'geocoded'
      ? '카카오 장소검색 좌표 · 실제 단지 위치'
      : '구 중심 좌표 기준 배치 · 단지 정밀 좌표 매핑 전'
  }));
}

function mockComplexItems(): TransactionItem[] {
  const mocks = seed.mockComplexes as Array<{
    id: string;
    name: string;
    region: string;
    gu: string;
    propertyType?: PropertyType;
    dealType: DealType;
    priceValue: number;
    dealCount: number;
    areaLabel: string;
    builtYear: number;
    lat: number;
    lng: number;
    tone: TransactionMapTone;
  }>;

  return mocks.map((mock) => ({
    id: mock.id,
    name: mock.name,
    region: mock.region,
    gu: mock.gu,
    propertyType: mock.propertyType ?? 'apt',
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
    tone: mock.tone,
    coordSource: 'approx'
  }));
}

type Fetcher = (input: string) => Promise<Response>;

export async function fetchTransactions(
  propertyType: PropertyType = 'apt',
  legalDongCode?: string,
  fetcher: Fetcher = fetch
): Promise<TransactionResult> {
  try {
    // Fetch only the selected category's factTypes (and region) so minority types
    // are never crowded out of a shared page.
    const factTypes = propertyFactTypes[propertyType];
    const factPages = await Promise.all(
      factTypes.map((factType) => fetchRealEstateMarketFacts({ factType, legalDongCode, limit: 500 }, fetcher))
    );
    const items = aggregateTransactions(factPages.flat());
    if (items.length) {
      return { items, source: 'live' };
    }
  } catch {
    // fall through to mock fallback
  }
  return { items: mockComplexItems().filter((item) => item.propertyType === propertyType), source: 'fallback' };
}
