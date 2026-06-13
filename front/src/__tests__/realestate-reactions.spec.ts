import { describe, expect, it, vi } from 'vitest';

import {
  buildRegionRankingRows,
  fetchRealEstateReactionRanking
} from '../lib/realestate-reactions';

describe('real-estate reaction ranking adapter', () => {
  it('fetches the latest reaction ranking for a target type', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ items: [] })));

    await fetchRealEstateReactionRanking({ type: 'region', windowMinutes: 60 }, fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/reactions/rankings?type=region&windowMinutes=60');
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
