export type IndicatorTone = 'up' | 'down' | 'neutral';

export type RealEstateIndicatorMetric = {
  name: string;
  value: string;
  tone: IndicatorTone;
};

export type RealEstateIndicatorGroup = {
  id: string;
  label: string;
  title: string;
  headline: string;
  change: string;
  tone: IndicatorTone;
  summary: string;
  chips: string[];
  metrics: RealEstateIndicatorMetric[];
  dataStatus?: string | null;
  stale?: boolean | null;
  provider?: string | null;
  asOf?: string | null;
};

export type IndicatorGroupFallback = Omit<RealEstateIndicatorGroup, 'dataStatus' | 'stale' | 'provider' | 'asOf'>;

export type IndicatorGroupView = RealEstateIndicatorGroup & {
  statusLabel: string;
};

export type RealEstateIndicatorFreshnessRow = {
  source: string;
  state: string;
  used: string;
};

export type RealEstateIndicatorOverview = {
  period: string;
  dataStatus: string;
  asOf?: string | null;
  groups: RealEstateIndicatorGroup[];
  freshnessRows: RealEstateIndicatorFreshnessRow[];
};

export async function fetchRealEstateIndicatorOverview(
  params: { legalDongCode?: string; period?: string } = {},
  fetcher: typeof fetch = fetch
): Promise<RealEstateIndicatorOverview> {
  const search = new URLSearchParams();
  if (params.legalDongCode) search.set('legalDongCode', params.legalDongCode);
  if (params.period) search.set('period', params.period);

  const query = search.toString();
  const response = await fetcher(`/api/realestate/indicators${query ? `?${query}` : ''}`);
  if (!response.ok) {
    throw new Error(`Failed to load real-estate indicators: ${response.status}`);
  }

  const payload = await response.json() as Partial<RealEstateIndicatorOverview>;
  return {
    period: payload.period ?? params.period ?? 'month',
    dataStatus: payload.dataStatus ?? 'unknown',
    asOf: payload.asOf ?? null,
    groups: Array.isArray(payload.groups) ? payload.groups.map(normalizeGroup) : [],
    freshnessRows: Array.isArray(payload.freshnessRows) ? payload.freshnessRows.map(normalizeFreshnessRow) : []
  };
}

export function mergeIndicatorGroups(
  apiGroups: RealEstateIndicatorGroup[],
  fallbackGroups: IndicatorGroupFallback[]
): IndicatorGroupView[] {
  const apiById = new Map(apiGroups.map((group) => [group.id, normalizeGroup(group)]));
  const usedIds = new Set<string>();

  const merged = fallbackGroups.map((fallback) => {
    const apiGroup = apiById.get(fallback.id);
    if (apiGroup) {
      usedIds.add(apiGroup.id);
      return {
        ...fallback,
        ...apiGroup,
        statusLabel: indicatorStatusLabel(apiGroup)
      };
    }

    return {
      ...fallback,
      dataStatus: 'mock',
      stale: true,
      provider: 'fixture',
      asOf: null,
      statusLabel: 'mock fallback'
    };
  });

  const appendedApiGroups = apiGroups
    .map(normalizeGroup)
    .filter((group) => !usedIds.has(group.id))
    .map((group) => ({
      ...group,
      statusLabel: indicatorStatusLabel(group)
    }));

  return [...merged, ...appendedApiGroups];
}

export function mergeIndicatorFreshnessRows(
  apiRows: RealEstateIndicatorFreshnessRow[],
  fallbackRows: RealEstateIndicatorFreshnessRow[]
): RealEstateIndicatorFreshnessRow[] {
  return apiRows.length > 0 ? apiRows.map(normalizeFreshnessRow) : fallbackRows;
}

export function indicatorStatusLabel(group: Pick<RealEstateIndicatorGroup, 'dataStatus' | 'stale'>): string {
  if (group.stale) return '지연 가능';
  const status = (group.dataStatus ?? '').toLowerCase();
  if (status === 'ok') return '공공데이터 반영';
  if (status === 'stale') return '지연 가능';
  if (status === 'empty') return '데이터 없음';
  if (status === 'mock') return 'mock fallback';
  if (status === 'error') return '확인 필요';
  return 'unknown';
}

function normalizeGroup(group: Partial<RealEstateIndicatorGroup>): RealEstateIndicatorGroup {
  return {
    id: group.id ?? 'unknown',
    label: group.label ?? 'indicator',
    title: group.title ?? '확인 필요',
    headline: group.headline ?? '데이터 확인이 필요합니다',
    change: group.change ?? 'unknown',
    tone: normalizeTone(group.tone),
    summary: group.summary ?? 'provider/asOf 확인이 필요합니다.',
    chips: Array.isArray(group.chips) ? group.chips : [],
    metrics: Array.isArray(group.metrics) ? group.metrics.map(normalizeMetric) : [],
    dataStatus: group.dataStatus ?? 'unknown',
    stale: Boolean(group.stale),
    provider: group.provider ?? null,
    asOf: group.asOf ?? null
  };
}

function normalizeMetric(metric: Partial<RealEstateIndicatorMetric>): RealEstateIndicatorMetric {
  return {
    name: metric.name ?? '확인 필요',
    value: metric.value ?? 'unknown',
    tone: normalizeTone(metric.tone)
  };
}

function normalizeFreshnessRow(row: Partial<RealEstateIndicatorFreshnessRow>): RealEstateIndicatorFreshnessRow {
  return {
    source: row.source ?? 'provider unknown',
    state: row.state ?? 'unknown',
    used: row.used ?? 'unknown'
  };
}

function normalizeTone(tone?: string | null): IndicatorTone {
  if (tone === 'down' || tone === 'neutral') return tone;
  return 'up';
}
