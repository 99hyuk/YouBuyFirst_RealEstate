import { describe, expect, it, vi } from 'vitest';

import {
  buildNewsroomFeedItems,
  fetchRealEstateNewsroom,
  fetchRealEstateTargetContent
} from '../lib/realestate-content';

describe('real-estate content adapter', () => {
  it('fetches newsroom content with UI feed mapped to backend content types', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ items: [] })));

    await fetchRealEstateNewsroom({ feed: 'reports', page: 2, pageSize: 15 }, fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/newsroom?feed=report&page=2&pageSize=15');
  });

  it('fetches target-scoped approved content', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ items: [] })));

    await fetchRealEstateTargetContent('region-seoul-jongno', { feed: 'links', limit: 12 }, fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-jongno/content?feed=link&limit=12');
  });

  it('maps backend content items to newsroom rows', () => {
    const rows = buildNewsroomFeedItems([
      {
        contentId: 'content-news-20260612-jongno',
        sourceId: 'ddangzipgo',
        contentType: 'news',
        title: '종로 도심 정비사업 후보지 발표',
        snippet: '정비사업 후보지가 공개되며 지역 커뮤니티 관심이 늘었습니다.',
        url: 'https://example.com/news/jongno-20260612',
        domain: 'example.com',
        publishedAt: '2026-06-12T04:00:00Z',
        metricLabel: '댓글 188',
        statusLabel: '링크 확인',
        ingestedAt: '2026-06-12T04:10:00Z',
        dataStatus: 'ok'
      },
      {
        contentId: 'content-video-20260612-jeonse',
        sourceId: 'youtube',
        contentType: 'video',
        title: '전세가 움직이는 지역을 장전에 확인하는 법',
        snippet: null,
        url: 'https://www.youtube.com/watch?v=demo',
        domain: 'www.youtube.com',
        publishedAt: '2026-06-11T12:00:00Z',
        metricLabel: '조회 4.8만',
        statusLabel: null,
        ingestedAt: '2026-06-12T04:10:00Z',
        dataStatus: 'mock'
      }
    ]);

    expect(rows).toEqual([
      {
        id: 'content-news-20260612-jongno',
        category: 'news',
        tone: 'news',
        title: '종로 도심 정비사업 후보지 발표',
        source: '땅집고',
        iconDomain: 'example.com',
        iconClass: 'news',
        url: 'https://example.com/news/jongno-20260612',
        meta: '2026-06-12 · 댓글 188',
        statusLabel: '링크 확인'
      },
      {
        id: 'content-video-20260612-jeonse',
        category: 'videos',
        tone: 'video',
        title: '전세가 움직이는 지역을 장전에 확인하는 법',
        source: '유튜브',
        iconDomain: 'www.youtube.com',
        iconClass: 'youtube',
        url: 'https://www.youtube.com/watch?v=demo',
        meta: '2026-06-11 · 조회 4.8만',
        statusLabel: 'mock',
        rankLabel: '1위'
      }
    ]);
  });
});
