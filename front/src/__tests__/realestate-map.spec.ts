import { describe, expect, it, vi } from 'vitest';

import { fetchRealEstateMapLayer } from '../lib/realestate-map';

describe('real-estate map API adapter', () => {
  it('fetches map layer snapshots with target ids and freshness metadata', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      layerType: 'sido',
      asOf: '2026-06-01T00:00:00Z',
      sourceLabel: 'map_layer_snapshots',
      mapDataSource: 'KOSTAT 2018',
      dataStatus: 'mock',
      stale: true,
      periods: ['week', 'month', 'halfYear'],
      targets: [
        {
          targetId: 'region-seoul',
          targetType: 'region',
          displayName: '서울특별시',
          slug: 'seoul',
          regionLevel: 'sido',
          regionCode: '11',
          geometryId: 'sido-11',
          periods: {
            month: {
              changePct: 0.62,
              sampleCount: 218,
              confidence: 82,
              asOf: '2026-06-01T00:00:00Z',
              provider: 'seed',
              dataStatus: 'mock',
              stale: true
            }
          }
        }
      ]
    }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200
    }));

    const response = await fetchRealEstateMapLayer({ layerType: 'sido' }, fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/map/layers?layerType=sido');
    expect(response.dataStatus).toBe('mock');
    expect(response.stale).toBe(true);
    expect(response.targets[0].targetId).toBe('region-seoul');
    expect(response.targets[0].periods.month?.changePct).toBe(0.62);
    expect(response.targets[0].periods.month?.provider).toBe('seed');
  });

  it('requests child map layers by parent target id', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      layerType: 'sigungu',
      parentTargetId: 'region-seoul',
      targets: []
    }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200
    }));

    await fetchRealEstateMapLayer({ layerType: 'sigungu', parentTargetId: 'region-seoul' }, fetcher);

    expect(fetcher).toHaveBeenCalledWith(
      '/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul'
    );
  });
});
