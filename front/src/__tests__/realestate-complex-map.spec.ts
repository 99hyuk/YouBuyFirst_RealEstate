import { describe, expect, it, vi } from 'vitest';

import { fetchRealEstateNearbyComplexes } from '../lib/realestate-complex-map';

describe('real-estate complex map API adapter', () => {
  it('maps verified nearby complex API rows and skips mock seed markers', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      items: [
        {
          targetId: 'complex-mapo-raemian-prugio',
          name: '마포래미안푸르지오',
          address: '서울 마포구 아현동',
          region: '서울 마포구',
          latitude: 37.5536,
          longitude: 126.9564,
          tone: 'up',
          price: '15.3억',
          change: '+0.21%',
          reaction: '커뮤니티 언급 증가',
          provider: 'complex_api_test',
          asOf: '2026-06-13T00:00:00Z',
          dataStatus: 'candidate',
          stale: true,
          note: 'API marker'
        },
        {
          targetId: 'complex-seed-marker',
          name: 'seed marker',
          latitude: 37.553,
          longitude: 126.956,
          provider: 'front_fixture',
          dataStatus: 'mock',
          stale: true,
          note: 'mock seed marker'
        }
      ]
    })));

    const markers = await fetchRealEstateNearbyComplexes('region-seoul-mapo', { limit: 10 }, fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/nearby-complexes?limit=10');
    expect(markers).toEqual([
      {
        targetId: 'complex-mapo-raemian-prugio',
        name: '마포래미안푸르지오',
        address: '서울 마포구 아현동',
        region: '서울 마포구',
        lat: 37.5536,
        lng: 126.9564,
        tone: 'up',
        price: '15.3억',
        change: '+0.21%',
        reaction: '커뮤니티 언급 증가',
        provider: 'complex_api_test',
        asOf: '2026-06-13',
        dataStatus: '좌표 후보 · 갱신 지연',
        note: 'API marker'
      }
    ]);
  });

  it('drops rows without usable coordinates', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      items: [
        { targetId: 'complex-without-coordinate', name: '좌표 없음' }
      ]
    })));

    await expect(fetchRealEstateNearbyComplexes('region-seoul-mapo', {}, fetcher))
      .resolves.toEqual([]);
  });
});
