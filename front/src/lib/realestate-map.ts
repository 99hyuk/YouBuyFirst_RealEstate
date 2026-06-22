import { repairMojibake } from './text-encoding';

export type PeriodKey = 'month' | 'quarter' | 'halfYear';

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
  if (!Array.isArray(periods)) return ['month', 'quarter', 'halfYear'];
  const allowed = new Set<PeriodKey>(['month', 'quarter', 'halfYear']);
  const normalized = periods.filter((period): period is PeriodKey => allowed.has(period as PeriodKey));
  return normalized.length ? normalized : ['month', 'quarter', 'halfYear'];
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
