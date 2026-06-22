import type { PeriodKey, RealEstateMapLayerPeriod, RealEstateMapLayerResponse } from './realestate-map';
import type { RealEstateReactionRanking, RealEstateReactionRankingItem } from './realestate-reactions';
import { repairMojibake } from './text-encoding';

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

export type IndicatorRegionTile = {
  name: string;
  targetId: string;
  direction: 'up' | 'down';
  change: string;
  heat: number;
  keyword: string;
  statusLabel: string;
};

export type IndicatorAnomalyRow = {
  target: string;
  targetId: string;
  type: string;
  price: string;
  reaction: string;
  reason: string;
  tone: 'up' | 'down' | 'neutral';
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
      dataStatus: 'planned',
      stale: true,
      provider: null,
      asOf: null,
      statusLabel: '연동 대기'
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
  return apiRows.length > 0
    ? apiRows.map(normalizeFreshnessRow)
    : fallbackRows.map((row) => ({
      source: row.source,
      state: '수집 전/insufficient',
      used: row.used
    }));
}

export function indicatorStatusLabel(group: Pick<RealEstateIndicatorGroup, 'dataStatus' | 'stale'>): string {
  if (group.stale) return '지연 가능';
  const status = (group.dataStatus ?? '').toLowerCase();
  if (status === 'ok') return '공공데이터 반영';
  if (status === 'stale') return '지연 가능';
  if (status === 'partial') return '부분 반영';
  if (status === 'insufficient') return '수집 전/insufficient';
  if (status === 'empty') return '데이터 없음';
  if (status === 'mock') return '수집 전/insufficient';
  if (status === 'planned') return '연동 대기';
  if (status === 'error') return '확인 필요';
  return 'unknown';
}

export function buildIndicatorRegionTiles(
  layer: RealEstateMapLayerResponse | null,
  period: PeriodKey = 'month',
  limit = 6
): IndicatorRegionTile[] {
  if (!layer?.targets?.length) return [];

  return layer.targets
    .map((target) => {
      const selectedPeriod = selectMapPeriod(target.periods, period);
      if (!isUsableMapPeriod(selectedPeriod)) return null;

      const changePct = selectedPeriod.changePct;
      return {
        name: target.displayName,
        targetId: target.targetId,
        direction: changePct >= 0 ? 'up' as const : 'down' as const,
        change: formatSignedPct(changePct),
        heat: heatFromChange(changePct, selectedPeriod.confidence),
        keyword: mapPeriodKeyword(selectedPeriod),
        statusLabel: indicatorStatusLabel({
          dataStatus: selectedPeriod.dataStatus,
          stale: selectedPeriod.stale
        })
      };
    })
    .filter((tile): tile is IndicatorRegionTile => tile !== null)
    .sort((a, b) => Math.abs(parseChange(b.change)) - Math.abs(parseChange(a.change)))
    .slice(0, limit);
}

export function buildIndicatorAnomalyRows(
  layer: RealEstateMapLayerResponse | null,
  ranking: RealEstateReactionRanking | null,
  period: PeriodKey = 'month',
  limit = 4
): IndicatorAnomalyRow[] {
  if (!ranking?.items?.length) return [];

  const mapTargets = new Map((layer?.targets ?? []).map((target) => [target.targetId, target]));

  return ranking.items
    .map((item) => {
      const mapTarget = mapTargets.get(item.targetId);
      const selectedPeriod = mapTarget ? selectMapPeriod(mapTarget.periods, period) : null;
      const hasMarketPeriod = isUsableMapPeriod(selectedPeriod);
      const reactionTone = reactionToneForItem(item);
      const marketTone = hasMarketPeriod
        ? selectedPeriod.changePct >= 0 ? 'up' as const : 'down' as const
        : 'neutral' as const;
      const isDivergent = hasMarketPeriod ? marketTone !== reactionTone : true;
      if (!isDivergent) return null;

      return {
        target: item.displayName,
        targetId: item.targetId,
        type: hasMarketPeriod
          ? `${marketTone === 'up' ? '지표 상승' : '지표 하락'} · ${reactionTone === 'up' ? '기대 우세' : '우려 우세'}`
          : '시장 사실 대기 · 반응만 관찰',
        price: hasMarketPeriod ? formatSignedPct(selectedPeriod.changePct) : '시장 사실 수집 전',
        reaction: reactionLabel(item),
        reason: anomalyReason(item, hasMarketPeriod ? selectedPeriod : null),
        tone: hasMarketPeriod ? marketTone : 'neutral'
      };
    })
    .filter((row): row is IndicatorAnomalyRow => row !== null)
    .slice(0, limit);
}

function selectMapPeriod(
  periods: Partial<Record<PeriodKey, RealEstateMapLayerPeriod>>,
  preferred: PeriodKey
): RealEstateMapLayerPeriod | null {
  return periods[preferred] ?? periods.month ?? periods.quarter ?? periods.halfYear ?? null;
}

function isUsableMapPeriod(period: RealEstateMapLayerPeriod | null | undefined): period is RealEstateMapLayerPeriod {
  if (!period) return false;
  const status = (period.dataStatus ?? '').toLowerCase();
  const provider = (period.provider ?? '').toLowerCase();
  const sourceLabel = (period.sourceLabel ?? '').toLowerCase();
  if (status === 'mock' || status === 'empty') return false;
  if (provider === 'seed' || provider.includes('fixture')) return false;
  if (provider === 'real_estate_reaction_snapshots' || provider === 'reaction_snapshots') return false;
  if (sourceLabel.includes('mock') || sourceLabel.includes('fixture')) return false;
  return Number.isFinite(period.changePct) && Number.isFinite(period.confidence);
}

function formatSignedPct(value: number): string {
  const normalized = Object.is(value, -0) ? 0 : value;
  const sign = normalized > 0 ? '+' : '';
  return `${sign}${normalized.toLocaleString('ko-KR', {
    maximumFractionDigits: 2,
    minimumFractionDigits: Math.abs(normalized) < 1 ? 2 : 1
  })}%`;
}

function parseChange(value: string): number {
  const parsed = Number(value.replace(/[+,%]/g, ''));
  return Number.isFinite(parsed) ? parsed : 0;
}

function heatFromChange(changePct: number, confidence: number): number {
  const intensity = Math.min(Math.abs(changePct) * 180, 70);
  const confidenceBoost = Math.max(0, Math.min(confidence, 1)) * 20;
  return Math.round(Math.min(100, Math.max(18, 18 + intensity + confidenceBoost)));
}

function mapPeriodKeyword(period: RealEstateMapLayerPeriod): string {
  if (period.sourceLabel?.trim()) return userFacingSourceLabel(period.sourceLabel);
  if (period.provider?.trim()) return period.provider;
  return period.sampleCount > 0 ? `표본 ${period.sampleCount}건` : '표본 확인 필요';
}

function reactionToneForItem(item: RealEstateReactionRankingItem): 'up' | 'down' {
  return item.reactionDirectionRatio.expectation >= item.reactionDirectionRatio.concern ? 'up' : 'down';
}

function reactionLabel(item: RealEstateReactionRankingItem): string {
  const expectation = Math.round(item.reactionDirectionRatio.expectation * 100);
  const concern = Math.round(item.reactionDirectionRatio.concern * 100);
  if (expectation === 0 && concern === 0) return '반응 비율 확인 필요';
  return expectation >= concern ? `기대 ${expectation}%` : `우려 ${concern}%`;
}

function anomalyReason(item: RealEstateReactionRankingItem, period: RealEstateMapLayerPeriod | null): string {
  const issue = item.issueMix?.[0]?.label;
  const quality = statusLabel(period?.dataStatus ?? item.coverageStatus);
  return [issue, quality].filter(Boolean).join(' · ');
}

function userFacingSourceLabel(label: string): string {
  return label
    .replace(/market fact/gi, '시장 사실')
    .replace(/heat/gi, '히트맵')
    .replace(/mock/gi, '수집 전')
    .replace(/fixture/gi, '수집 전');
}

function statusLabel(status?: string | null): string {
  const normalized = (status ?? '').toLowerCase();
  if (normalized === 'low_sample') return '표본 부족';
  if (normalized === 'partial') return '부분 반영';
  if (normalized === 'insufficient') return '수집 전';
  if (normalized === 'empty') return '데이터 없음';
  if (normalized === 'stale') return '갱신 지연';
  if (normalized === 'ok') return '공공데이터 반영';
  return status || '수집 상태 확인 필요';
}

function normalizeGroup(group: Partial<RealEstateIndicatorGroup>): RealEstateIndicatorGroup {
  return {
    id: repairMojibake(group.id) || 'unknown',
    label: repairMojibake(group.label) || 'indicator',
    title: repairMojibake(group.title) || '확인 필요',
    headline: repairMojibake(group.headline) || '데이터 확인이 필요합니다',
    change: repairMojibake(group.change) || '확인 필요',
    tone: normalizeTone(group.tone),
    summary: repairMojibake(group.summary) || '출처와 기준 시각 확인이 필요합니다.',
    chips: Array.isArray(group.chips) ? group.chips.map(repairMojibake) : [],
    metrics: Array.isArray(group.metrics) ? group.metrics.map(normalizeMetric) : [],
    dataStatus: repairMojibake(group.dataStatus) || '확인 필요',
    stale: Boolean(group.stale),
    provider: repairMojibake(group.provider) || null,
    asOf: repairMojibake(group.asOf) || null
  };
}

function normalizeMetric(metric: Partial<RealEstateIndicatorMetric>): RealEstateIndicatorMetric {
  return {
    name: repairMojibake(metric.name) || '확인 필요',
    value: repairMojibake(metric.value) || '확인 필요',
    tone: normalizeTone(metric.tone)
  };
}

function normalizeFreshnessRow(row: Partial<RealEstateIndicatorFreshnessRow>): RealEstateIndicatorFreshnessRow {
  return {
    source: repairMojibake(row.source) || '출처 확인 필요',
    state: repairMojibake(row.state) || '상태 확인 필요',
    used: repairMojibake(row.used) || '사용처 확인 필요'
  };
}

function normalizeTone(tone?: string | null): IndicatorTone {
  if (tone === 'down' || tone === 'neutral') return tone;
  return 'up';
}
