import type { PeriodKey, RealEstateMapLayerResponse } from './realestate-map';
import type { RealEstateReactionRankingItem } from './realestate-reactions';

export type DashboardReturnMode = PeriodKey | 'year';

export type DashboardSpeculationHeat = {
  label: string;
  value: number;
  unit: string;
  changePct: number | null;
  changeLabel: string;
  keywords: string[];
  status: string;
  segments: { label: string; start: number; end: number; color: string }[];
  dataStatus: string;
};

export type DashboardRegionalMomentumRow = {
  targetId: string;
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
  { id: 'week', label: '주' },
  { id: 'month', label: '월' },
  { id: 'halfYear', label: '6개월' },
  { id: 'year', label: '년' }
];

const heatSegments = [
  { label: '냉각', start: 0, end: 35, color: '#dbe4ef' },
  { label: '관망', start: 35, end: 55, color: '#f3dfc9' },
  { label: '주의', start: 55, end: 75, color: '#f59e0b' },
  { label: '과열', start: 75, end: 90, color: '#ef4444' },
  { label: '투기 과열', start: 90, end: 100, color: '#b91c1c' }
];

export function buildDashboardSpeculationHeat(
  items: RealEstateReactionRankingItem[]
): DashboardSpeculationHeat {
  if (!items.length) {
    return {
      label: '부동산 투기 과열 지표',
      value: 0,
      unit: '점',
      changePct: null,
      changeLabel: '최근 24시간',
      keywords: ['반응 수집 대기', '표본 부족'],
      status: '수집 전',
      segments: heatSegments,
      dataStatus: 'insufficient'
    };
  }

  const topItems = items.slice(0, 5);
  const mentionTotal = topItems.reduce((sum, item) => sum + Math.max(item.mentionCount, 1), 0);
  const weightedHeat = topItems.reduce(
    (sum, item) => sum + item.heatScore * Math.max(item.mentionCount, 1),
    0
  ) / mentionTotal;
  const weightedMentionDelta = topItems.reduce(
    (sum, item) => sum + item.mentionDeltaPct * Math.max(item.mentionCount, 1),
    0
  ) / mentionTotal;
  const concernShare = topItems.reduce(
    (sum, item) => sum + item.reactionDirectionRatio.concern * Math.max(item.mentionCount, 1),
    0
  ) / mentionTotal;
  const pressureBonus = Math.min(Math.max(weightedMentionDelta, 0), 120) * 0.12 + concernShare * 14;
  const value = clampScore(Math.round(weightedHeat * 0.82 + pressureBonus));

  return {
    label: '부동산 투기 과열 지표',
    value,
    unit: '점',
    changePct: roundOne(weightedMentionDelta),
    changeLabel: '최근 24시간 평균 증가율',
    keywords: aggregateIssues(topItems),
    status: heatStatus(value),
    segments: heatSegments,
    dataStatus: topItems.some((item) => item.stale) ? 'stale' : coverageStatus(topItems)
  };
}

export function buildRegionalMomentumRows(
  layer: RealEstateMapLayerResponse | null,
  period: DashboardReturnMode,
  limit = 6
): DashboardRegionalMomentumRow[] {
  if (!layer || period === 'year') return [];

  const rows = layer.targets
    .map((target) => {
      const periodMeta = target.periods[period];
      if (!periodMeta) return null;
      return {
        targetId: target.targetId,
        name: target.displayName,
        changePct: roundTwo(periodMeta.changePct),
        sampleCount: periodMeta.sampleCount,
        confidence: periodMeta.confidence,
        provider: periodMeta.provider ?? layer.sourceLabel ?? 'provider 확인 필요',
        asOf: periodMeta.asOf ?? layer.asOf ?? '기준 시각 확인 필요',
        dataStatus: periodMeta.dataStatus ?? layer.dataStatus ?? 'unknown',
        stale: Boolean(periodMeta.stale ?? layer.stale),
        barPct: 0,
        tone: periodMeta.changePct >= 0 ? 'up' : 'down'
      } satisfies DashboardRegionalMomentumRow;
    })
    .filter((row): row is DashboardRegionalMomentumRow => row !== null)
    .sort((left, right) => right.changePct - left.changePct)
    .slice(0, limit);

  const maxAbs = Math.max(...rows.map((row) => Math.abs(row.changePct)), 0.01);
  return rows.map((row) => ({
    ...row,
    barPct: Math.max(8, Math.round((Math.abs(row.changePct) / maxAbs) * 100))
  }));
}

export function dashboardReturnModeLabel(period: DashboardReturnMode): string {
  if (period === 'week') return '최근 1주';
  if (period === 'month') return '최근 1개월';
  if (period === 'halfYear') return '최근 6개월';
  return '최근 1년';
}

function aggregateIssues(items: RealEstateReactionRankingItem[]): string[] {
  const weights = new Map<string, number>();
  for (const item of items) {
    for (const issue of item.issueMix) {
      weights.set(issue.label, (weights.get(issue.label) ?? 0) + issue.share * Math.max(item.mentionCount, 1));
    }
  }

  const labels = [...weights.entries()]
    .sort((left, right) => right[1] - left[1])
    .slice(0, 3)
    .map(([label]) => label);

  return labels.length ? labels : ['쟁점 분류 대기', '표본 보강 필요'];
}

function coverageStatus(items: RealEstateReactionRankingItem[]): string {
  if (items.some((item) => item.coverageStatus === 'source_skewed')) return 'source_skewed';
  if (items.some((item) => item.coverageStatus === 'partial')) return 'partial';
  return items[0]?.coverageStatus ?? 'unknown';
}

function heatStatus(value: number): string {
  if (value >= 90) return '투기 과열 관찰';
  if (value >= 75) return '과열 관찰';
  if (value >= 60) return '주의 구간';
  if (value >= 40) return '관심 증가';
  return '관망';
}

function clampScore(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function roundOne(value: number): number {
  return Math.round(value * 10) / 10;
}

function roundTwo(value: number): number {
  return Math.round(value * 100) / 100;
}
