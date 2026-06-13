import { describe, expect, it, vi } from 'vitest';

import { fetchRealEstateNearbyComplexes } from '../lib/realestate-complex-map';

describe('real-estate complex map API adapter', () => {
  it('maps nearby complex API rows to embedded map markers', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      items: [
        {
          targetId: 'complex-mapo-raemian-prugio',
          name: '마포래미안푸르지오',
          address: '서울 마포구 아현동 일대',
          region: '서울 마포구',
          latitude: 37.5536,
          longitude: 126.9564,
          tone: 'up',
          price: '15.3억',
          change: '+0.21%',
          reaction: '학군·전세권 언급 증가',
          provider: 'front_fixture',
          asOf: '2026-06-13T00:00:00Z',
          dataStatus: 'mock',
          stale: true,
          note: '검증용 marker'
        }
      ]
    })));

    const markers = await fetchRealEstateNearbyComplexes('region-seoul-mapo', { limit: 10 }, fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/nearby-complexes?limit=10');
    expect(markers).toEqual([
      {
        targetId: 'complex-mapo-raemian-prugio',
        name: '마포래미안푸르지오',
        address: '서울 마포구 아현동 일대',
        region: '서울 마포구',
        lat: 37.5536,
        lng: 126.9564,
        tone: 'up',
        price: '15.3억',
        change: '+0.21%',
        reaction: '학군·전세권 언급 증가',
        provider: 'front_fixture',
        asOf: '2026-06-13',
        dataStatus: 'mock · stale',
        note: '검증용 marker'
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
