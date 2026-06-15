import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  buildRegionRankingRows,
  fetchRealEstateReactionRanking
} from '../lib/realestate-reactions';
import RegionReactionPage from '../pages/RegionReactionPage.vue';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('real-estate reaction ranking adapter', () => {
  it('fetches the latest daily reaction ranking for a target type by default', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ items: [] })));

    await fetchRealEstateReactionRanking({
      type: 'region',
      limit: 10,
      parentTargetId: 'region-seoul'
    }, fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/reactions/rankings?type=region&windowMinutes=1440&limit=10&parentTargetId=region-seoul');
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

  it('uses live region ranking rows for the community pulse cards', async () => {
    const fetcher = vi.fn(async (input: string) => {
      if (input.includes('type=region')) {
        return new Response(JSON.stringify({
          items: [
            {
              rank: 1,
              targetId: 'region-seoul',
              targetType: 'region',
              displayName: '서울특별시',
              mentionCount: 18,
              mentionDeltaPct: 100,
              reactionDirectionRatio: { expectation: 0.06, concern: 0.06, neutral: 0.88 },
              heatScore: 100,
              confidence: 0.87,
              sourceCount: 1,
              sourceSkew: 1,
              coverageStatus: 'source_skewed',
              stale: false,
              issueMix: [
                { issueKey: 'jeonse', label: '전세', share: 0.06, direction: 'concern', summary: '전세 우려', confidence: 0.78 }
              ]
            }
          ]
        }));
      }

      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/realestate/reactions', component: RegionReactionPage },
        { path: '/realestate/targets/:targetId', component: { template: '<div />' } }
      ]
    });
    router.push('/realestate/reactions');
    await router.isReady();

    const wrapper = mount(RegionReactionPage, {
      global: {
        plugins: [router]
      }
    });
    await flushPromises();

    const signalBoardText = wrapper.find('.region-signal-overview-board').text();
    expect(signalBoardText).toContain('서울특별시');
    expect(signalBoardText).toContain('+100%');
    expect(signalBoardText).not.toContain('성수동 생활권');
  });
});
