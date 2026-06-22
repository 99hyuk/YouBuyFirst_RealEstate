import { describe, expect, it } from 'vitest';

import { buildRegionalMomentumRows } from '../lib/realestate-dashboard';

describe('real-estate dashboard adapters', () => {
  it('builds regional momentum rows from map layer snapshots', () => {
    const rows = buildRegionalMomentumRows({
      layerType: 'sido',
      asOf: '2026-06-01T00:00:00Z',
      sourceLabel: 'map_layer_snapshots',
      dataStatus: 'ok',
      stale: false,
      periods: ['month', 'quarter', 'halfYear'],
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
      periods: ['month', 'quarter', 'halfYear'],
      targets: []
    }, 'year');

    expect(rows).toEqual([]);
  });

  it('does not treat reaction-only map periods as regional price momentum', () => {
    const rows = buildRegionalMomentumRows({
      layerType: 'sido',
      periods: ['month', 'quarter', 'halfYear'],
      targets: [
        {
          targetId: 'region-seoul',
          targetType: 'region',
          displayName: '서울특별시',
          regionCode: '11',
          periods: {
            quarter: {
              changePct: 0.65,
              sampleCount: 21,
              confidence: 86,
              provider: 'real_estate_reaction_snapshots',
              asOf: '2026-06-01',
              dataStatus: 'partial',
              stale: false
            }
          }
        }
      ]
    }, 'quarter');

    expect(rows).toEqual([]);
  });
});
