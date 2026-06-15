import { describe, expect, it } from 'vitest';

import {
  buildDashboardSpeculationHeat,
  buildRegionalMomentumRows
} from '../lib/realestate-dashboard';

describe('real-estate dashboard adapters', () => {
  it('derives the speculation heat gauge from live reaction ranking rows', () => {
    const heat = buildDashboardSpeculationHeat([
      {
        rank: 1,
        targetId: 'region-seoul',
        targetType: 'region',
        displayName: '서울특별시',
        mentionCount: 120,
        mentionDeltaPct: 80,
        reactionDirectionRatio: { expectation: 0.48, concern: 0.34, neutral: 0.18 },
        heatScore: 76,
        confidence: 0.86,
        sourceCount: 4,
        sourceSkew: 0.33,
        coverageStatus: 'partial',
        stale: false,
        issueMix: [
          { issueKey: 'jeonse', label: '전세', share: 0.4, direction: 'concern', confidence: 0.8 },
          { issueKey: 'transport', label: '교통', share: 0.22, direction: 'expectation', confidence: 0.7 }
        ]
      }
    ]);

    expect(heat.label).toBe('부동산 투기 과열 지표');
    expect(heat.value).toBeGreaterThan(0);
    expect(heat.changePct).toBe(80);
    expect(heat.keywords).toEqual(['전세', '교통']);
    expect(heat.dataStatus).toBe('partial');
  });

  it('keeps the speculation heat gauge explicit when no ranking rows exist', () => {
    const heat = buildDashboardSpeculationHeat([]);

    expect(heat.value).toBe(0);
    expect(heat.status).toBe('수집 전');
    expect(heat.dataStatus).toBe('insufficient');
  });

  it('builds regional momentum rows from map layer snapshots', () => {
    const rows = buildRegionalMomentumRows({
      layerType: 'sido',
      asOf: '2026-06-01T00:00:00Z',
      sourceLabel: 'map_layer_snapshots',
      dataStatus: 'ok',
      stale: false,
      periods: ['week', 'month', 'halfYear'],
      targets: [
        {
          targetId: 'region-seoul',
          targetType: 'region',
          displayName: '서울특별시',
          regionCode: '11',
          periods: {
            month: {
              changePct: 0.72,
              sampleCount: 200,
              confidence: 88,
              provider: 'molit',
              asOf: '2026-06-01',
              dataStatus: 'ok',
              stale: false
            }
          }
        },
        {
          targetId: 'region-busan',
          targetType: 'region',
          displayName: '부산광역시',
          regionCode: '26',
          periods: {
            month: {
              changePct: -0.21,
              sampleCount: 40,
              confidence: 62,
              provider: 'molit',
              asOf: '2026-06-01',
              dataStatus: 'stale',
              stale: true
            }
          }
        }
      ]
    }, 'month');

    expect(rows).toEqual([
      expect.objectContaining({
        targetId: 'region-seoul',
        name: '서울특별시',
        changePct: 0.72,
        barPct: 100,
        tone: 'up'
      }),
      expect.objectContaining({
        targetId: 'region-busan',
        name: '부산광역시',
        changePct: -0.21,
        stale: true,
        tone: 'down'
      })
    ]);
  });

  it('does not invent annual momentum before the yearly snapshot exists', () => {
    const rows = buildRegionalMomentumRows({
      layerType: 'sido',
      periods: ['week', 'month', 'halfYear'],
      targets: []
    }, 'year');

    expect(rows).toEqual([]);
  });
});
