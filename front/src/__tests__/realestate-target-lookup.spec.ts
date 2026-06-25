import { describe, expect, it, vi } from 'vitest';

import { fetchRealEstateTargetIdByName } from '../lib/realestate-target-lookup';

describe('real-estate target lookup adapter', () => {
  it('returns null without calling the API for a blank name', async () => {
    const fetcher = vi.fn();

    const targetId = await fetchRealEstateTargetIdByName('   ', fetcher);

    expect(targetId).toBeNull();
    expect(fetcher).not.toHaveBeenCalled();
  });

  it('searches by name and returns the first matching targetId', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      items: [{ targetId: 'region-seoul-mapo', targetType: 'region', displayName: '마포구' }]
    })));

    const targetId = await fetchRealEstateTargetIdByName('마포구', fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/search?q=%EB%A7%88%ED%8F%AC%EA%B5%AC&limit=5');
    expect(targetId).toBe('region-seoul-mapo');
  });

  it('prefers a complex-type match over a region match when both are returned', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      items: [
        { targetId: 'region-seoul-mapo', targetType: 'region', displayName: '마포구' },
        { targetId: 'complex-molit-1111011500-sajik-palace', targetType: 'complex', displayName: '사직팰리스' }
      ]
    })));

    const targetId = await fetchRealEstateTargetIdByName('사직팰리스', fetcher);

    expect(targetId).toBe('complex-molit-1111011500-sajik-palace');
  });

  it('returns null when no targets match', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ items: [] })));

    const targetId = await fetchRealEstateTargetIdByName('존재하지않는단지', fetcher);

    expect(targetId).toBeNull();
  });

  it('throws when the search request fails', async () => {
    const fetcher = vi.fn(async () => new Response('error', { status: 500 }));

    await expect(fetchRealEstateTargetIdByName('마포구', fetcher)).rejects.toThrow();
  });
});
