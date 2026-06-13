export type RealEstateMarketFact = {
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
  factType?: string;
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

export async function fetchRealEstateMarketFacts(
  params: FetchMarketFactParams = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateMarketFact[]> {
  const query = new URLSearchParams();
  if (params.legalDongCode) query.set('legalDongCode', params.legalDongCode);
  if (params.factType) query.set('factType', params.factType);

  const suffix = query.toString();
  const response = await fetcher(`/api/realestate/market-facts${suffix ? `?${suffix}` : ''}`);
  if (!response.ok) {
    throw new Error(`market facts request failed: ${response.status}`);
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
    label: item.label,
    value: item.value,
    changePct: typeof item.changePct === 'number' ? item.changePct : null,
    updatedLabel: item.updatedLabel,
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
  return [
    fact.providerDataset ?? 'market-fact',
    fact.legalDongCode ?? 'unknown',
    fact.factType ?? 'unknown',
    fact.observedAt ?? fact.asOf ?? 'unknown'
  ].join(':');
}

export function marketFactStatusLabel(fact: Pick<RealEstateMarketFact, 'dataStatus' | 'stale'>): string {
  if (fact.stale) return '지연 가능';
  const status = (fact.dataStatus ?? '').toLowerCase();
  if (status === 'ok') return '공공데이터 반영';
  if (status === 'mock') return 'mock';
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
  const name = stringValue(valueJson.apartmentName) ?? '단지명 확인 필요';
  const observedAt = fact.observedAt ?? '계약일 확인 필요';
  const asOf = fact.asOf ?? '기준일 확인 필요';
  return `${name} · 계약 ${observedAt} · 기준 ${asOf}`;
}

function providerLabel(provider?: string): string {
  if (provider === 'molit') return '국토교통부';
  return provider ?? 'provider 확인 필요';
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
