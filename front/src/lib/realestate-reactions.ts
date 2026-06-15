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
  parentTargetId?: string;
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

export async function fetchRealEstateReactionRanking(
  params: FetchRealEstateReactionRankingParams = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateReactionRanking> {
  const query = new URLSearchParams();
  query.set('type', params.type ?? 'region');
  query.set('windowMinutes', String(params.windowMinutes ?? 1440));
  if (params.windowStart) query.set('windowStart', params.windowStart);
  if (params.limit) query.set('limit', String(params.limit));
  if (params.parentTargetId) query.set('parentTargetId', params.parentTargetId);

  const response = await fetcher(`/api/realestate/reactions/rankings?${query.toString()}`);
  if (!response.ok) {
    throw new Error(`reaction ranking request failed: ${response.status}`);
  }
  const payload = await response.json() as Partial<RealEstateReactionRanking>;
  return {
    window: payload.window,
    windowStart: payload.windowStart,
    windowEnd: payload.windowEnd,
    freshness: payload.freshness,
    items: Array.isArray(payload.items) ? payload.items : []
  };
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
    return {
      rank: item.rank,
      name: item.displayName,
      targetId: item.targetId,
      market: targetTypeLabel(item.targetType),
      price: '시장 데이터 대기',
      change: item.stale ? '지연' : '관찰',
      mentions: `${item.mentionCount.toLocaleString('ko-KR')}건`,
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
  if (item.stale) return `수집 지연 · ${item.coverageStatus}`;
  return `출처 ${item.sourceCount}곳 · 신뢰 ${Math.round(item.confidence * 100)}%`;
}
