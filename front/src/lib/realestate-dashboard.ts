import type { PeriodKey, RealEstateMapLayerPeriod, RealEstateMapLayerResponse } from './realestate-map';

export type DashboardReturnMode = PeriodKey | 'year';

export type DashboardRegionalMomentumRow = {
  targetId: string;
  parentTargetId?: string | null;
  regionCode: string;
  geometryId?: string | null;
  name: string;
  changePct: number;
  sampleCount: number;
  confidence: number;
  provider: string;
  asOf: string;
  dataStatus: string;
  stale: boolean;
  barPct: number;
  tone: 'up' | 'down';
};

export const dashboardReturnModes: { id: DashboardReturnMode; label: string }[] = [
  { id: 'month', label: '월' },
  { id: 'quarter', label: '3개월' },
  { id: 'halfYear', label: '6개월' },
  { id: 'year', label: '년' }
];

export function buildRegionalMomentumRows(
  layer: RealEstateMapLayerResponse | null,
  period: DashboardReturnMode,
  limit = 6
): DashboardRegionalMomentumRow[] {
  if (!layer || period === 'year') return [];

  const rows = layer.targets
    .flatMap((target) => {
      const periodMeta = target.periods[period];
      if (!isPriceMomentumPeriod(periodMeta)) return [];
      const row: DashboardRegionalMomentumRow = {
        targetId: target.targetId,
        parentTargetId: target.parentTargetId,
        regionCode: target.regionCode,
        geometryId: target.geometryId,
        name: target.displayName,
        changePct: roundTwo(periodMeta.changePct),
        sampleCount: periodMeta.sampleCount,
        confidence: periodMeta.confidence,
        provider: dashboardProviderLabel(periodMeta.provider ?? layer.sourceLabel),
        asOf: periodMeta.asOf ?? layer.asOf ?? '기준 시각 확인 필요',
        dataStatus: periodMeta.dataStatus ?? layer.dataStatus ?? '확인 필요',
        stale: Boolean(periodMeta.stale ?? layer.stale),
        barPct: 0,
        tone: periodMeta.changePct >= 0 ? 'up' : 'down'
      };
      return [row];
    })
    .sort((left, right) => right.changePct - left.changePct)
    .slice(0, limit);

  const maxAbs = Math.max(...rows.map((row) => Math.abs(row.changePct)), 0.01);
  return rows.map((row) => ({
    ...row,
    barPct: Math.max(8, Math.round((Math.abs(row.changePct) / maxAbs) * 100))
  }));
}

function isPriceMomentumPeriod(
  period?: RealEstateMapLayerResponse['targets'][number]['periods'][PeriodKey]
): period is RealEstateMapLayerPeriod {
  if (!period) return false;
  const provider = (period.provider ?? '').toLowerCase();
  const status = (period.dataStatus ?? '').toLowerCase();
  if (status === 'mock' || status === 'empty') return false;
  return provider !== 'seed'
    && provider !== 'real_estate_reaction_snapshots'
    && provider !== 'reaction_snapshots';
}

function dashboardProviderLabel(provider?: string | null): string {
  const normalized = provider?.trim();
  if (!normalized) return '출처 확인 필요';
  const labels: Record<string, string> = {
    real_estate_reaction_snapshots: '반응 지표',
    reaction_snapshots: '반응 지표',
    map_layer_snapshots: '지도 흐름 자료',
    market_facts: '시장 사실',
    molit: '국토교통부',
    reb: '한국부동산원',
    reb_rone_weekly_apt_sale_price_index_region: '한국부동산원',
    reb_stat: '한국부동산원'
  };
  return labels[normalized] ?? normalized.replace(/_/g, ' ');
}

export function dashboardReturnModeLabel(period: DashboardReturnMode): string {
  if (period === 'month') return '최근 1개월';
  if (period === 'quarter') return '최근 3개월';
  if (period === 'halfYear') return '최근 6개월';
  return '최근 1년';
}

function roundTwo(value: number): number {
  return Math.round(value * 100) / 100;
}
