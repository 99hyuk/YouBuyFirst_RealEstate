import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  buildRegionRankingRows,
  fetchRealEstateReactionRanking,
  fetchRealEstateReactionRankingWithFallback,
  reactionRankingWindowLabel
} from '../lib/realestate-reactions';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('real-estate reaction ranking adapter', () => {
  it('fetches the latest daily reaction ranking for a target type by default', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ items: [] })));

    await fetchRealEstateReactionRanking({
      type: 'region',
      limit: 10
    }, fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/reactions/rankings?type=region&windowMinutes=10080&limit=10');
  });

  it('falls back to the latest 60 minute ranking when the daily ranking is empty', async () => {
    const fetcher = vi.fn(async (input: string) => {
      if (input.includes('windowMinutes=10080')) {
        return new Response(JSON.stringify({ window: '10080m', items: [] }));
      }

      return new Response(JSON.stringify({
        window: '60m',
        items: [
          {
            rank: 1,
            targetId: 'region-seoul-mapo',
            targetType: 'region',
            displayName: '마포구',
            mentionCount: 2,
            mentionDeltaPct: 100,
            reactionDirectionRatio: { expectation: 0, concern: 0.5, neutral: 0.5 },
            heatScore: 40,
            confidence: 0.36,
            sourceCount: 1,
            sourceSkew: 1,
            coverageStatus: 'low_sample',
            stale: false,
            issueMix: []
          }
        ]
      }));
    });

    const ranking = await fetchRealEstateReactionRankingWithFallback({ type: 'region', windowMinutes: 10080, limit: 10 }, fetcher);

    expect(fetcher).toHaveBeenNthCalledWith(1, '/api/realestate/reactions/rankings?type=region&windowMinutes=10080&limit=10');
    expect(fetcher).toHaveBeenNthCalledWith(2, '/api/realestate/reactions/rankings?type=region&windowMinutes=60&limit=10');
    expect(ranking.items).toHaveLength(1);
    expect(ranking.usedFallbackWindow).toBe(true);
    expect(reactionRankingWindowLabel(ranking)).toBe('1시간 · 7일 부족분 보정');
  });

  it('keeps region rankings focused on child regions instead of broad city/province rollups', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      window: '10080m',
      items: [
        {
          rank: 1,
          targetId: 'region-seoul',
          targetType: 'region',
          displayName: '서울특별시',
          mentionCount: 80,
          mentionDeltaPct: 50,
          reactionDirectionRatio: { expectation: 0.4, concern: 0.3, neutral: 0.3 },
          heatScore: 90,
          confidence: 0.8,
          sourceCount: 4,
          sourceSkew: 0.3,
          coverageStatus: 'partial',
          stale: false,
          issueMix: []
        },
        {
          rank: 2,
          targetId: 'region-seoul-mapo',
          targetType: 'region',
          displayName: '마포구',
          mentionCount: 42,
          mentionDeltaPct: 35,
          reactionDirectionRatio: { expectation: 0.55, concern: 0.2, neutral: 0.25 },
          heatScore: 76,
          confidence: 0.74,
          sourceCount: 3,
          sourceSkew: 0.44,
          coverageStatus: 'partial',
          stale: false,
          issueMix: []
        },
        {
          rank: 3,
          targetId: 'region-seoul-mapo-ahyeon',
          targetType: 'region',
          displayName: '아현동',
          mentionCount: 27,
          mentionDeltaPct: 22,
          reactionDirectionRatio: { expectation: 0.5, concern: 0.25, neutral: 0.25 },
          heatScore: 64,
          confidence: 0.66,
          sourceCount: 2,
          sourceSkew: 0.5,
          coverageStatus: 'partial',
          stale: false,
          issueMix: []
        }
      ]
    })));

    const ranking = await fetchRealEstateReactionRankingWithFallback({
      type: 'region',
      windowMinutes: 10080,
      limit: 10
    }, fetcher);

    expect(ranking.items.map((item) => item.targetId)).toEqual([
      'region-seoul-mapo',
      'region-seoul-mapo-ahyeon'
    ]);
    expect(ranking.items.map((item) => item.rank)).toEqual([1, 2]);
  });

  it('keeps complex rankings limited to actual apartment complex targets', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      window: '10080m',
      items: [
        {
          rank: 1,
          targetId: 'region-seoul-mapo',
          targetType: 'region',
          displayName: '마포구',
          mentionCount: 50,
          mentionDeltaPct: 30,
          reactionDirectionRatio: { expectation: 0.4, concern: 0.3, neutral: 0.3 },
          heatScore: 70,
          confidence: 0.7,
          sourceCount: 2,
          sourceSkew: 0.5,
          coverageStatus: 'partial',
          stale: false,
          issueMix: []
        },
        {
          rank: 2,
          targetId: 'complex-molit-1111011500-sajik-palace',
          targetType: 'complex',
          displayName: '사직팰리스',
          mentionCount: 16,
          mentionDeltaPct: 120,
          reactionDirectionRatio: { expectation: 0.6, concern: 0.18, neutral: 0.22 },
          heatScore: 82,
          confidence: 0.72,
          sourceCount: 3,
          sourceSkew: 0.42,
          coverageStatus: 'partial',
          stale: false,
          issueMix: []
        }
      ]
    })));

    const ranking = await fetchRealEstateReactionRankingWithFallback({ type: 'complex', windowMinutes: 10080, limit: 10 }, fetcher);

    expect(ranking.items.map((item) => item.targetId)).toEqual([
      'complex-molit-1111011500-sajik-palace'
    ]);
    expect(ranking.items[0].rank).toBe(1);
  });

  it('maps backend reaction rows to the region reaction table shape', () => {
    const rows = buildRegionRankingRows({
      window: '60m',
      windowStart: '2026-06-11T00:00:00Z',
      windowEnd: '2026-06-11T01:00:00Z',
      freshness: {
        source: 'real_estate_reaction_snapshots',
        asOf: '2026-06-11T01:02:00Z',
        staleCount: 0,
        sourceCount: 4,
        coverageStatus: 'partial'
      },
      items: [
        {
          rank: 1,
          targetId: 'region-seoul-jongno',
          targetType: 'region',
          displayName: '서울 종로구',
          mentionCount: 128,
          mentionDeltaPct: 45.5,
          reactionDirectionRatio: { expectation: 0.57, concern: 0.25, neutral: 0.18 },
          heatScore: 82,
          confidence: 0.78,
          sourceCount: 4,
          sourceSkew: 0.42,
          coverageStatus: 'partial',
          stale: false,
          issueMix: [
            { issueKey: 'jeonse', label: '전세', share: 0.41, direction: 'concern', summary: '전세 매물 우려', confidence: 0.82 },
            { issueKey: 'school', label: '학군', share: 0.24, direction: 'expectation', summary: '학군 기대', confidence: 0.71 }
          ]
        }
      ]
    }, []);

    expect(rows).toEqual([
      {
        rank: 1,
        name: '서울 종로구',
        targetId: 'region-seoul-jongno',
        market: '지역',
        price: '시장 데이터 대기',
        change: '관찰',
        mentions: '128건',
        mentionDelta: '+45.5%',
        positive: 57,
        negative: 25,
        event: '전세·학군',
        freshness: '출처 4곳 · 신뢰 78%',
        tone: 'up'
      }
    ]);
  });
});
