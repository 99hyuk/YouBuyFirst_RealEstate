import { repairMojibake } from './text-encoding';

export type RealEstateReactionIssue = {
  issueKey: string;
  label: string;
  share: number;
  direction: string;
  summary?: string | null;
  confidence: number;
};

export type RealEstateReactionRankingItem = {
  rank: number;
  targetId: string;
  targetType: string;
  displayName: string;
  mentionCount: number;
  mentionDeltaPct: number;
  reactionDirectionRatio: {
    expectation: number;
    concern: number;
    neutral: number;
  };
  heatScore: number;
  confidence: number;
  sourceCount: number;
  sourceSkew: number;
  coverageStatus: string;
  stale: boolean;
  issueMix: RealEstateReactionIssue[];
};

export type RealEstateReactionRanking = {
  window?: string;
  windowStart?: string | null;
  windowEnd?: string | null;
  requestedWindowMinutes?: number;
  fallbackFromWindowMinutes?: number | null;
  usedFallbackWindow?: boolean;
  usedMapLayerFallback?: boolean;
  freshness?: {
    source?: string;
    asOf?: string | null;
    staleCount?: number;
    sourceCount?: number;
    coverageStatus?: string;
  };
  items: RealEstateReactionRankingItem[];
};

export type FetchRealEstateReactionRankingParams = {
  type?: string;
  windowMinutes?: number;
  windowStart?: string;
  limit?: number;
};

export type RegionReactionRankingRow = {
  rank: number;
  name: string;
  targetId: string;
  market: string;
  price: string;
  change: string;
  mentions: string;
  mentionDelta: string;
  positive: number;
  negative: number;
  event: string;
  freshness: string;
  tone: 'up' | 'down';
};

type Fetcher = (input: string) => Promise<Response>;

export const DEFAULT_REACTION_WINDOW_MINUTES = 10080;

export async function fetchRealEstateReactionRanking(
  params: FetchRealEstateReactionRankingParams = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateReactionRanking> {
  const query = new URLSearchParams();
  query.set('type', params.type ?? 'region');
  query.set('windowMinutes', String(params.windowMinutes ?? DEFAULT_REACTION_WINDOW_MINUTES));
  if (params.windowStart) query.set('windowStart', params.windowStart);
  if (params.limit) query.set('limit', String(params.limit));

  const response = await fetcher(`/api/realestate/reactions/rankings?${query.toString()}`);
  if (!response.ok) {
    throw new Error(`reaction ranking request failed: ${response.status}`);
  }
  const payload = await response.json() as Partial<RealEstateReactionRanking>;
  return {
    window: payload.window,
    windowStart: payload.windowStart,
    windowEnd: payload.windowEnd,
    requestedWindowMinutes: params.windowMinutes ?? DEFAULT_REACTION_WINDOW_MINUTES,
    fallbackFromWindowMinutes: null,
    usedFallbackWindow: false,
    freshness: payload.freshness,
    items: normalizeRankingItemsForParams(
      Array.isArray(payload.items) ? payload.items.map(normalizeRankingItem) : [],
      params
    )
  };
}

export async function fetchRealEstateReactionRankingWithFallback(
  params: FetchRealEstateReactionRankingParams = {},
  fetcher: Fetcher = fetch,
  fallbackWindowMinutes = 60
): Promise<RealEstateReactionRanking> {
  const requestedWindowMinutes = params.windowMinutes ?? DEFAULT_REACTION_WINDOW_MINUTES;
  const primary = await fetchRealEstateReactionRanking({ ...params, windowMinutes: requestedWindowMinutes }, fetcher);
  if (primary.items.length || params.windowStart || requestedWindowMinutes === fallbackWindowMinutes) {
    return primary;
  }

  const fallback = await fetchRealEstateReactionRanking({
    ...params,
    windowMinutes: fallbackWindowMinutes
  }, fetcher);

  if (!fallback.items.length) {
    return primary;
  }

  return {
    ...fallback,
    requestedWindowMinutes: fallbackWindowMinutes,
    fallbackFromWindowMinutes: requestedWindowMinutes,
    usedFallbackWindow: true
  };
}

export function reactionRankingWindowLabel(ranking?: RealEstateReactionRanking | null): string {
  if (!ranking) return '기간 확인 필요';
  const windowLabel = ranking.window ?? `${ranking.requestedWindowMinutes ?? DEFAULT_REACTION_WINDOW_MINUTES}m`;
  const readableWindowLabel = readableWindow(windowLabel);
  if (ranking.usedFallbackWindow && ranking.fallbackFromWindowMinutes) {
    return `${readableWindowLabel} · ${readableWindow(`${ranking.fallbackFromWindowMinutes}m`)} 부족분 보정`;
  }
  if (ranking.usedMapLayerFallback) {
    return `${readableWindowLabel} · 시장 지표 보강`;
  }
  return readableWindowLabel;
}

export function buildRegionRankingRows(
  ranking: RealEstateReactionRanking,
  fallbackRows: RegionReactionRankingRow[]
): RegionReactionRankingRow[] {
  if (!ranking.items.length) {
    return fallbackRows;
  }

  return ranking.items.map((item) => {
    const expectation = ratioPercent(item.reactionDirectionRatio.expectation);
    const concern = ratioPercent(item.reactionDirectionRatio.concern);
    const marketDataOnly = item.coverageStatus === 'market_data_only';
    return {
      rank: item.rank,
      name: item.displayName,
      targetId: item.targetId,
      market: targetTypeLabel(item.targetType),
      price: marketDataOnly ? '공식 지표 기반' : '시장 데이터 대기',
      change: item.stale ? '지연' : marketDataOnly ? formatDelta(item.mentionDeltaPct) : '관찰',
      mentions: marketDataOnly ? '반응 부족' : `${item.mentionCount.toLocaleString('ko-KR')}건`,
      mentionDelta: formatDelta(item.mentionDeltaPct),
      positive: expectation,
      negative: concern,
      event: issueLabel(item.issueMix),
      freshness: freshnessLabel(item),
      tone: expectation >= concern ? 'up' : 'down'
    };
  });
}

function targetTypeLabel(targetType: string): string {
  if (targetType === 'complex') return '단지';
  if (targetType === 'living_area') return '생활권';
  if (targetType === 'policy_area') return '정책권';
  return '지역';
}

function normalizeRankingItem(item: RealEstateReactionRankingItem): RealEstateReactionRankingItem {
  return {
    ...item,
    displayName: repairMojibake(item.displayName),
    coverageStatus: repairMojibake(item.coverageStatus),
    issueMix: Array.isArray(item.issueMix) ? item.issueMix.map(normalizeIssue) : []
  };
}

function normalizeRankingItemsForParams(
  items: RealEstateReactionRankingItem[],
  params: FetchRealEstateReactionRankingParams
): RealEstateReactionRankingItem[] {
  const requestedType = params.type ?? 'region';
  const filtered = items.filter((item) => {
    if (requestedType === 'complex') return item.targetType === 'complex';
    if (requestedType !== 'region') return item.targetType === requestedType;
    if (item.targetType !== 'region' && item.targetType !== 'living_area') return false;
    return !BROAD_REGION_TARGET_IDS.has(item.targetId);
  });

  return filtered.map((item, index) => ({
    ...item,
    rank: index + 1
  }));
}

const BROAD_REGION_TARGET_IDS = new Set([
  'region-seoul',
  'region-busan',
  'region-daegu',
  'region-incheon',
  'region-gwangju',
  'region-daejeon',
  'region-ulsan',
  'region-sejong',
  'region-gyeonggi',
  'region-gangwon',
  'region-chungbuk',
  'region-chungnam',
  'region-jeonbuk',
  'region-jeonnam',
  'region-gyeongbuk',
  'region-gyeongnam',
  'region-jeju'
]);

function normalizeIssue(issue: RealEstateReactionIssue): RealEstateReactionIssue {
  return {
    ...issue,
    label: repairMojibake(issue.label),
    summary: repairMojibake(issue.summary),
    direction: repairMojibake(issue.direction)
  };
}

function readableWindow(label: string): string {
  const match = label.match(/^(\d+)m$/);
  if (!match) return label;
  const minutes = Number(match[1]);
  if (!Number.isFinite(minutes)) return label;
  if (minutes % 1440 === 0) return `${minutes / 1440}일`;
  if (minutes % 60 === 0) return `${minutes / 60}시간`;
  return `${minutes}분`;
}

function ratioPercent(value: number): number {
  return Math.round(value * 100);
}

function formatDelta(value: number): string {
  return `${value > 0 ? '+' : ''}${value.toLocaleString('ko-KR', {
    maximumFractionDigits: 1
  })}%`;
}

function issueLabel(issues: RealEstateReactionIssue[]): string {
  if (!issues.length) return '쟁점 확인 필요';
  return issues.slice(0, 3).map((issue) => issue.label).join('·');
}

function freshnessLabel(item: RealEstateReactionRankingItem): string {
  if (item.coverageStatus === 'market_data_only') return '시장 지표 보강 · 반응 부족';
  if (item.stale) return `수집 지연 · ${coverageStatusLabel(item.coverageStatus)}`;
  return `출처 ${item.sourceCount}곳 · 신뢰 ${Math.round(item.confidence * 100)}%`;
}

function coverageStatusLabel(status: string): string {
  if (status === 'market_data_only') return '시장 지표 보강';
  if (status === 'source_skewed') return '출처 편중';
  if (status === 'partial') return '부분 반영';
  if (status === 'low_sample') return '표본 부족';
  if (status === 'ok') return '수집 확인';
  if (status === 'empty' || status === 'insufficient' || status === 'mock') return '수집 전';
  if (status === 'stale') return '갱신 지연';
  return status || '확인 필요';
}
