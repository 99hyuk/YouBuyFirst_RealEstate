import { repairMojibake } from './text-encoding';

export type PeriodKey = 'week' | 'month' | 'quarter' | 'halfYear' | 'year';

export type RealEstateMapLayerPeriod = {
  changePct: number;
  sampleCount: number;
  confidence: number;
  asOf?: string | null;
  provider?: string | null;
  sourceLabel?: string | null;
  dataStatus?: string | null;
  stale?: boolean;
};

export type RealEstateMapLayerTarget = {
  targetId: string;
  targetType: string;
  displayName: string;
  slug?: string | null;
  regionLevel?: string | null;
  regionCode: string;
  legalDongCode?: string | null;
  parentTargetId?: string | null;
  geometryId?: string | null;
  periods: Partial<Record<PeriodKey, RealEstateMapLayerPeriod>>;
};

export type RealEstateMapLayerResponse = {
  layerType: string;
  parentTargetId?: string | null;
  parentRegionCode?: string | null;
  asOf?: string | null;
  sourceLabel?: string | null;
  mapDataSource?: string | null;
  dataStatus?: string | null;
  stale?: boolean;
  periods: PeriodKey[];
  targets: RealEstateMapLayerTarget[];
};

export type FetchRealEstateMapLayerParams = {
  layerType?: 'sido' | 'sigungu' | 'eupmyeondong';
  parentTargetId?: string;
};

export type MapHeatTone = 'up' | 'down' | 'flat';

export type MapHeatScale = {
  baselineChangePct: number;
  maxDeltaPct: number;
};

type Fetcher = (input: string) => Promise<Response>;

export async function fetchRealEstateMapLayer(
  params: FetchRealEstateMapLayerParams = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateMapLayerResponse> {
  const query = new URLSearchParams();
  query.set('layerType', params.layerType ?? 'sido');
  if (params.parentTargetId) query.set('parentTargetId', params.parentTargetId);

  const response = await fetcher(`/api/realestate/map/layers?${query.toString()}`);
  if (!response.ok) {
    throw new Error(`map layer request failed: ${response.status}`);
  }

  const payload = await response.json() as Partial<RealEstateMapLayerResponse>;
  return {
    layerType: payload.layerType ?? params.layerType ?? 'sido',
    parentTargetId: repairMojibake(payload.parentTargetId),
    parentRegionCode: repairMojibake(payload.parentRegionCode),
    asOf: repairMojibake(payload.asOf),
    sourceLabel: repairMojibake(payload.sourceLabel),
    mapDataSource: repairMojibake(payload.mapDataSource),
    dataStatus: repairMojibake(payload.dataStatus),
    stale: Boolean(payload.stale),
    periods: normalizePeriods(payload.periods),
    targets: Array.isArray(payload.targets) ? payload.targets.map(normalizeTarget).filter(isMapLayerTarget) : []
  };
}

function normalizePeriods(periods: unknown): PeriodKey[] {
  if (!Array.isArray(periods)) return ['week', 'month', 'quarter', 'halfYear', 'year'];
  const allowed = new Set<PeriodKey>(['week', 'month', 'quarter', 'halfYear', 'year']);
  const normalized = periods.filter((period): period is PeriodKey => allowed.has(period as PeriodKey));
  return normalized.length ? normalized : ['week', 'month', 'quarter', 'halfYear', 'year'];
}

function normalizeTarget(target: RealEstateMapLayerTarget): RealEstateMapLayerTarget | null {
  if (!target?.targetId || !target.regionCode) return null;
  return {
    targetId: target.targetId,
    targetType: target.targetType ?? 'region',
    displayName: repairMojibake(target.displayName) || target.targetId,
    slug: target.slug,
    regionLevel: repairMojibake(target.regionLevel),
    regionCode: target.regionCode,
    legalDongCode: target.legalDongCode,
    parentTargetId: target.parentTargetId,
    geometryId: target.geometryId,
    periods: normalizeLayerPeriods(target.periods ?? {})
  };
}

function normalizeLayerPeriods(
  periods: Partial<Record<PeriodKey, RealEstateMapLayerPeriod>>
): Partial<Record<PeriodKey, RealEstateMapLayerPeriod>> {
  return Object.fromEntries(
    Object.entries(periods)
      .filter((entry): entry is [string, RealEstateMapLayerPeriod] => Boolean(entry[1]))
      .map(([key, period]) => [
        key,
        {
          ...period,
          asOf: repairMojibake(period.asOf),
          provider: repairMojibake(period.provider),
          sourceLabel: repairMojibake(period.sourceLabel),
          dataStatus: repairMojibake(period.dataStatus)
        }
      ])
  ) as Partial<Record<PeriodKey, RealEstateMapLayerPeriod>>;
}

function isMapLayerTarget(target: RealEstateMapLayerTarget | null): target is RealEstateMapLayerTarget {
  return target !== null;
}

export function buildMapHeatScale(values: number[], baselineChangePct?: number): MapHeatScale {
  const usableValues = values.filter((value) => Number.isFinite(value));
  const baseline = Number.isFinite(baselineChangePct)
    ? baselineChangePct as number
    : average(usableValues);
  const maxDelta = usableValues.reduce(
    (currentMax, value) => Math.max(currentMax, Math.abs(value - baseline)),
    0
  );

  return {
    baselineChangePct: baseline,
    maxDeltaPct: Math.max(0.01, maxDelta)
  };
}

export function mapHeatTone(changePct: number): MapHeatTone {
  if (changePct > 0.04) return 'up';
  if (changePct < -0.04) return 'down';
  return 'flat';
}

export function mapHeatColor(changePct: number, scale: MapHeatScale = buildMapHeatScale([changePct], 0)): string {
  const tone = mapHeatTone(changePct);
  if (tone === 'flat') return 'rgba(126, 143, 166, 0.420)';

  const delta = Math.abs(changePct - scale.baselineChangePct);
  const intensity = Math.min(1, Math.max(0.12, delta / scale.maxDeltaPct));
  const minimumVisibleAlpha = 0.56;
  if (tone === 'up') return `rgba(255, 54, 88, ${formatAlpha(Math.max(minimumVisibleAlpha, 0.3 + intensity * 0.66))})`;
  return `rgba(42, 125, 255, ${formatAlpha(Math.max(minimumVisibleAlpha, 0.28 + intensity * 0.62))})`;
}

function average(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function formatAlpha(value: number): string {
  return value.toFixed(3);
}
