import { describe, expect, it, vi } from 'vitest';

import {
  buildMapHeatScale,
  fetchRealEstateMapLayer,
  mapHeatColor,
  mapHeatTone
} from '../lib/realestate-map';

describe('real-estate map API adapter', () => {
  it('fetches map layer snapshots with target ids and freshness metadata', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      layerType: 'sido',
      asOf: '2026-06-01T00:00:00Z',
      sourceLabel: 'map_layer_snapshots',
      mapDataSource: 'KOSTAT 2018',
      dataStatus: 'mock',
      stale: true,
      periods: ['week', 'month', 'quarter', 'halfYear', 'year'],
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
            week: {
              changePct: 0.14,
              sampleCount: 1,
              confidence: 95,
              asOf: '2026-06-01T00:00:00Z',
              provider: 'reb_rone_weekly_apt_sale_price_index_region',
              dataStatus: 'ok',
              stale: false
            },
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
    expect(response.periods).toEqual(['week', 'month', 'quarter', 'halfYear', 'year']);
    expect(response.targets[0].targetId).toBe('region-seoul');
    expect(response.targets[0].periods.week?.changePct).toBe(0.14);
    expect(response.targets[0].periods.week?.provider).toBe('reb_rone_weekly_apt_sale_price_index_region');
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

describe('real-estate map heat scale', () => {
  it('uses visible map calculations and national baseline to control color intensity', () => {
    const scale = buildMapHeatScale([0.24, 0.45, -0.12], 0.24);

    expect(mapHeatTone(0.45)).toBe('up');
    expect(mapHeatTone(-0.12)).toBe('down');
    expect(mapHeatColor(0.25, scale)).toBe('rgba(255, 54, 88, 0.560)');
    expect(mapHeatColor(0.45, scale)).toBe('rgba(255, 54, 88, 0.685)');
    expect(mapHeatColor(-0.12, scale)).toBe('rgba(42, 125, 255, 0.900)');
  });

  it('keeps small official non-flat movements visibly colored on compact map regions', () => {
    const scale = buildMapHeatScale([-0.2, -0.21, 0.5], -0.2);

    expect(mapHeatTone(-0.21)).toBe('down');
    expect(mapHeatColor(-0.21, scale)).toBe('rgba(42, 125, 255, 0.560)');
  });

  it('keeps nearly flat regions neutral while still scaling stronger regional changes', () => {
    const scale = buildMapHeatScale([0.01, 0.09, -0.05], 0);

    expect(mapHeatTone(0.01)).toBe('flat');
    expect(mapHeatColor(0.01, scale)).toBe('rgba(126, 143, 166, 0.420)');
    expect(mapHeatColor(0.09, scale)).toBe('rgba(255, 54, 88, 0.960)');
  });
});
