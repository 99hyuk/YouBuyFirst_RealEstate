import { repairMojibake } from './text-encoding';

export type RealEstateMarketFact = {
  providerObjectId?: string;
  factType?: string;
  provider?: string;
  providerDataset?: string;
  legalDongCode?: string | null;
  observedAt?: string | null;
  asOf?: string | null;
  valueJson?: Record<string, unknown> | null;
  dataStatus?: string | null;
  stale?: boolean;
};

export type RealEstateMarketFactRow = {
  id: string;
  name: string;
  value: string;
  meta: string;
  providerLabel: string;
  statusLabel: string;
  stale: boolean;
};

export type FetchMarketFactParams = {
  legalDongCode?: string;
  targetId?: string;
  factType?: string;
  officialOnly?: boolean;
  limit?: number;
  page?: number;
};

type Fetcher = (input: string) => Promise<Response>;

export type RealEstateMarketSummaryItem = {
  label: string;
  value: string;
  changePct?: number | null;
  updatedLabel: string;
  trend: string;
  dataStatus?: string | null;
  stale?: boolean;
  provider?: string;
  factType?: string;
  legalDongCode?: string | null;
};

export type RealEstateMarketSummary = {
  items: RealEstateMarketSummaryItem[];
  freshness?: {
    staleCount?: number;
    sourceCount?: number;
    latestAsOf?: string | null;
    dataStatus?: string | null;
  };
};

export type RealEstateMarketIndicatorCard = {
  label: string;
  value: string;
  changePct: number | null;
  updatedLabel: string;
  trend: string;
};

export const realEstateMarketIndicatorFallbacks: RealEstateMarketIndicatorCard[] = [
  {
    label: '공급·수급',
    value: '미분양·공급 후보',
    changePct: null,
    updatedLabel: '공공데이터 연동 대기',
    trend: 'down'
  },
  {
    label: '수요·심리',
    value: '반응 지표 기반',
    changePct: null,
    updatedLabel: '커뮤니티 반응 보조',
    trend: 'up'
  },
  {
    label: '거시·금융',
    value: '금리·대출 이슈',
    changePct: null,
    updatedLabel: '최근 이슈 후보',
    trend: 'up'
  }
];

export async function fetchRealEstateMarketFacts(
  params: FetchMarketFactParams = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateMarketFact[]> {
  const query = new URLSearchParams();
  if (params.legalDongCode) query.set('legalDongCode', params.legalDongCode);
  if (params.targetId) query.set('targetId', params.targetId);
  if (params.factType) query.set('factType', params.factType);
  if (typeof params.limit === 'number') query.set('limit', String(params.limit));
  if (typeof params.page === 'number') query.set('page', String(params.page));

  const suffix = query.toString();
  const response = await fetcher(`/api/realestate/market-facts${suffix ? `?${suffix}` : ''}`);
  if (!response.ok) {
    throw new Error(`market facts request failed: ${response.status}`);
  }
  const payload = await response.json() as { items?: RealEstateMarketFact[] };
  return Array.isArray(payload.items) ? payload.items : [];
}

export async function fetchRealEstateTargetMarketFacts(
  targetId: string,
  params: Pick<FetchMarketFactParams, 'factType' | 'limit' | 'officialOnly'> = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateMarketFact[]> {
  const query = new URLSearchParams();
  if (params.factType) query.set('factType', params.factType);
  if (typeof params.limit === 'number') query.set('limit', String(params.limit));
  if (params.officialOnly) query.set('officialOnly', 'true');

  const suffix = query.toString();
  const response = await fetcher(`/api/realestate/targets/${encodeURIComponent(targetId)}/market-facts${suffix ? `?${suffix}` : ''}`);
  if (!response.ok) {
    throw new Error(`target market facts request failed: ${response.status}`);
  }
  const payload = await response.json() as { items?: RealEstateMarketFact[] };
  return Array.isArray(payload.items) ? payload.items : [];
}

export async function fetchRealEstateMarketSummary(
  params: Pick<FetchMarketFactParams, 'legalDongCode'> = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateMarketSummary> {
  const query = new URLSearchParams();
  if (params.legalDongCode) query.set('legalDongCode', params.legalDongCode);

  const suffix = query.toString();
  const response = await fetcher(`/api/realestate/dashboard/market-summary${suffix ? `?${suffix}` : ''}`);
  if (!response.ok) {
    throw new Error(`market summary request failed: ${response.status}`);
  }
  const payload = await response.json() as Partial<RealEstateMarketSummary>;
  return {
    items: Array.isArray(payload.items) ? payload.items : [],
    freshness: payload.freshness
  };
}

export function buildMarketSummaryIndicators(
  summary: RealEstateMarketSummary,
  fallbackIndicators: RealEstateMarketIndicatorCard[] = []
): RealEstateMarketIndicatorCard[] {
  const apiIndicators = summary.items.map((item) => ({
    label: repairMojibake(item.label),
    value: repairMojibake(item.value),
    changePct: typeof item.changePct === 'number' ? item.changePct : null,
    updatedLabel: repairMojibake(item.updatedLabel),
    trend: item.trend === 'down' ? 'down' : 'up'
  }));

  if (!apiIndicators.length) {
    return fallbackIndicators;
  }
  return [
    ...apiIndicators,
    ...fallbackIndicators.filter((item) => !apiIndicators.some((apiItem) => apiItem.label === item.label))
  ];
}

export function buildMarketFactRows(facts: RealEstateMarketFact[]): RealEstateMarketFactRow[] {
  if (!facts.length) {
    return [{
      id: 'empty-market-facts',
      name: '실거래·전월세',
      value: '수집 대기',
      meta: '공공데이터 registry 연결 후 표시',
      providerLabel: '국토교통부',
      statusLabel: '데이터 없음',
      stale: true
    }];
  }

  const baseIds = facts.map(marketFactBaseId);
  const baseIdCounts = baseIds.reduce((counts, id) => counts.set(id, (counts.get(id) ?? 0) + 1), new Map<string, number>());
  const seenBaseIds = new Map<string, number>();

  return facts.map((fact, index) => {
    const baseId = baseIds[index];
    const occurrenceIndex = seenBaseIds.get(baseId) ?? 0;
    seenBaseIds.set(baseId, occurrenceIndex + 1);
    const valueJson = fact.valueJson ?? {};
    return {
      id: (baseIdCounts.get(baseId) ?? 0) > 1 ? `${baseId}:${occurrenceIndex + 1}` : baseId,
      name: factName(fact),
      value: factValue(fact, valueJson),
      meta: factMeta(fact, valueJson),
      providerLabel: providerLabel(fact.provider),
      statusLabel: marketFactStatusLabel(fact),
      stale: Boolean(fact.stale)
    };
  });
}

function marketFactBaseId(fact: RealEstateMarketFact): string {
  const parts = [
    fact.providerDataset ?? 'market-fact',
    fact.legalDongCode ?? 'unknown',
    fact.factType ?? 'unknown',
    fact.observedAt ?? fact.asOf ?? 'unknown'
  ];
  if (fact.providerObjectId) {
    parts.splice(1, 0, fact.providerObjectId);
  }
  return parts.join(':');
}

export function marketFactStatusLabel(fact: Pick<RealEstateMarketFact, 'dataStatus' | 'stale'>): string {
  if (fact.stale) return '지연 가능';
  const status = (fact.dataStatus ?? '').toLowerCase();
  if (status === 'ok') return '공공데이터 반영';
  if (status === 'mock') return '수집 전/insufficient';
  if (status === 'insufficient') return '수집 전/insufficient';
  if (status === 'empty') return '데이터 없음';
  return '확인 필요';
}

function factName(fact: RealEstateMarketFact): string {
  if (fact.factType === 'apt_trade') return '매매 실거래';
  if (fact.factType === 'apt_rent') return '전월세 실거래';
  return '시장 사실';
}

function factValue(fact: RealEstateMarketFact, valueJson: Record<string, unknown>): string {
  if (fact.factType === 'apt_trade') {
    const dealAmount = numberValue(valueJson.dealAmountManwon);
    return dealAmount === null ? '금액 확인 필요' : formatManwonAsEok(dealAmount);
  }

  if (fact.factType === 'apt_rent') {
    const deposit = numberValue(valueJson.depositAmountManwon) ?? numberValue(valueJson.depositManwon);
    const monthlyRent = numberValue(valueJson.monthlyRentAmountManwon) ?? numberValue(valueJson.monthlyRentManwon);
    const depositLabel = deposit === null ? '보증금 확인 필요' : `보증금 ${formatManwonAsEok(deposit)}`;
    const rentLabel = monthlyRent === null ? '월세 확인 필요' : `월세 ${monthlyRent.toLocaleString('ko-KR')}만원`;
    return `${depositLabel} / ${rentLabel}`;
  }

  return '값 확인 필요';
}

function factMeta(fact: RealEstateMarketFact, valueJson: Record<string, unknown>): string {
  const name = repairMojibake(stringValue(valueJson.apartmentName)) || '단지명 확인 필요';
  const observedAt = repairMojibake(fact.observedAt) || '계약일 확인 필요';
  const asOf = repairMojibake(fact.asOf) || '기준일 확인 필요';
  const exclusiveArea = numberValue(valueJson.exclusiveAreaM2);
  const floor = numberValue(valueJson.floor);
  return [
    name,
    exclusiveArea === null ? null : `전용 ${exclusiveArea.toLocaleString('ko-KR', { maximumFractionDigits: 2 })}㎡`,
    floor === null ? null : `${floor}층`,
    `계약 ${observedAt}`,
    `기준 ${asOf}`
  ].filter((item): item is string => Boolean(item)).join(' · ');
}

function providerLabel(provider?: string): string {
  if (provider === 'molit') return '국토교통부';
  return provider ?? '출처 확인 필요';
}

function formatManwonAsEok(value: number): string {
  return `${(value / 10000).toLocaleString('ko-KR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}억원`;
}

function numberValue(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  return null;
}

function stringValue(value: unknown): string | null {
  if (typeof value === 'string' && value.trim()) return value;
  return null;
}
