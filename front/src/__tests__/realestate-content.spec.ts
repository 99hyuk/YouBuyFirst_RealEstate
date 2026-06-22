import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  buildNewsroomFeedItems,
  ensureNewsroomCategoryCoverage,
  fetchRealEstateNewsroom,
  fetchRealEstateTargetContent
} from '../lib/realestate-content';

describe('real-estate content adapter', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

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
        statusLabel: '수집 전/insufficient'
      }
    ]);
  });

  it('keeps newsroom categories grounded in content source instead of cloning news rows', () => {
    const rows = ensureNewsroomCategoryCoverage(buildNewsroomFeedItems([
      {
        contentId: 'serpapi-news-seoul-jeonse',
        sourceId: 'serpapi:google_news',
        contentType: 'news',
        title: '서울 전세난 심화 속 주거비 부담 확산',
        snippet: '전세 매물이 줄었다는 뉴스 기사입니다.',
        url: 'https://www.hankyung.com/realestate/article/demo',
        domain: 'www.hankyung.com',
        metricLabel: 'query: 서울특별시 전세 부동산',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-report-kb-market',
        sourceId: 'serpapi:google_news',
        contentType: 'news',
        title: 'KB부동산 월간 주택시장 리포트 발표',
        snippet: '금융사 리서치 자료가 공개됐습니다.',
        url: 'https://www.kbstar.com/report/demo',
        domain: 'www.kbstar.com',
        metricLabel: 'query: 서울특별시 리포트 부동산',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-video-sejong',
        sourceId: 'serpapi:google_news',
        contentType: 'news',
        title: '세종 주택시장 유튜브 해설 - 집코노미',
        snippet: '집코노미 정책 해설 영상 후보입니다.',
        url: 'https://www.youtube.com/watch?v=sejong-demo',
        domain: 'www.youtube.com',
        metricLabel: 'query: 세종특별자치시 영상 부동산',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-column-jeju',
        sourceId: 'serpapi:google_news',
        contentType: 'news',
        title: '제주 부동산 정책 블로그 해설',
        snippet: '블로그 후보입니다.',
        url: 'https://blog.naver.com/demo/jeju',
        domain: 'blog.naver.com',
        metricLabel: 'query: 제주특별자치도 블로그 부동산',
        statusLabel: 'search_candidate'
      }
    ]));

    expect(rows.map((row) => row.category)).toEqual(['news', 'reports', 'videos', 'links']);
    expect(rows).toHaveLength(4);
    expect(rows[0].source).toBe('한국경제');
    expect(rows[0].statusLabel).toBe('근거 후보');
    expect(rows[1].source).toBe('KB국민은행');
    expect(rows[1].iconClass).toBe('news-research');
  });

  it('drops non-youtube search results from video-intent queries even when text says video', () => {
    const rows = buildNewsroomFeedItems([
      {
        contentId: 'serpapi-video-looking-news',
        sourceId: 'serpapi:google_news',
        contentType: 'news',
        title: '서울 부동산 영상 브리핑 기사',
        snippet: '영상이라는 표현이 있지만 언론 기사 페이지입니다.',
        url: 'https://www.hankyung.com/realestate/article/demo',
        domain: 'www.hankyung.com',
        metricLabel: 'query: 서울특별시 영상 부동산',
        statusLabel: 'search_candidate'
      }
    ]);

    expect(rows).toHaveLength(0);
  });

  it('filters obvious search noise from candidate feeds', () => {
    const rows = buildNewsroomFeedItems([
      {
        contentId: 'serpapi-job-post',
        sourceId: 'serpapi:google_news',
        contentType: 'video',
        title: '부동산 채널 유튜브 PD 채용',
        snippet: '채용 공고입니다.',
        url: 'https://www.jobkorea.co.kr/Recruit/GI_Read/demo',
        domain: 'www.jobkorea.co.kr',
        metricLabel: 'query: 서울특별시 유튜브 부동산',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-youtube-wrapper',
        sourceId: 'serpapi:google_news',
        contentType: 'news',
        title: 'YOUTUBE 영상 보기',
        snippet: '공유용 래퍼 페이지입니다.',
        url: 'https://gogogogo.kr/share/youtube/EcoJ8VurLhc',
        domain: 'gogogogo.kr',
        metricLabel: 'query: 경기도 유튜브 부동산',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-news-valid',
        sourceId: 'serpapi:google_news',
        contentType: 'news',
        title: '인천 주거 정책 후보',
        snippet: '정책 기사입니다.',
        url: 'https://www.newsfreezone.co.kr/news/articleView.html?idxno=1',
        domain: 'www.newsfreezone.co.kr',
        metricLabel: 'query: 인천광역시 뉴스 부동산',
        statusLabel: 'search_candidate'
      }
    ]);

    expect(rows).toHaveLength(1);
    expect(rows[0].id).toBe('serpapi-news-valid');
    expect(rows[0].category).toBe('news');
  });

  it('does not treat media articles quoting finance brands as policy reports', () => {
    const rows = buildNewsroomFeedItems([
      {
        contentId: 'serpapi-media-kb-quote',
        sourceId: 'serpapi:google_news',
        contentType: 'report',
        title: 'KB부동산 "경기 남부 아파트값 강세…동탄 상승폭 역대 최고"',
        snippet: '언론사가 KB부동산 발언을 인용한 기사입니다.',
        url: 'https://news.einfomax.co.kr/news/articleView.html?idxno=4419533',
        domain: 'news.einfomax.co.kr',
        metricLabel: 'query: 경기도 부동산',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-kb-report',
        sourceId: 'serpapi:google_news',
        contentType: 'news',
        title: 'KB부동산 주간 주택시장 리포트',
        snippet: '금융사 리서치 자료입니다.',
        url: 'https://www.kbstar.com/report/demo',
        domain: 'www.kbstar.com',
        metricLabel: 'query: 경기도 리포트 부동산',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-media-report-launch',
        sourceId: 'serpapi:google_news',
        contentType: 'report',
        title: 'KB금융, 부동산 시장 진단 담은 보고서 발간',
        snippet: '언론사가 보고서 발간 소식을 다룬 기사입니다.',
        url: 'https://www.handmk.com/news/articleView.html?idxno=37730',
        domain: 'www.handmk.com',
        metricLabel: 'query: 경기도 KB부동산 리포트 부동산',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-video-job-post',
        sourceId: 'serpapi:google_news',
        contentType: 'video',
        title: '부동산 채널 유튜브 PD 채용',
        snippet: '채용 공고입니다.',
        url: 'https://www.jobkorea.co.kr/Recruit/GI_Read/demo',
        domain: 'www.jobkorea.co.kr',
        metricLabel: 'query: 서울특별시 유튜브 부동산',
        statusLabel: 'search_candidate'
      }
    ]);

    expect(rows.map((row) => row.category)).toEqual(['news', 'reports', 'news']);
    expect(rows.map((row) => row.id)).not.toContain('serpapi-video-job-post');
  });

  it('keeps trusted real-estate analysis youtube candidates and drops listing videos', () => {
    const rows = buildNewsroomFeedItems([
      {
        contentId: 'serpapi-youtube-analysis',
        sourceId: 'serpapi:google_news',
        contentType: 'video',
        title: '서울 부동산 시장 전망 토론 - 집코노미',
        snippet: '집코노미가 전세와 공급 흐름을 분석합니다.',
        url: 'https://www.youtube.com/watch?v=analysis',
        domain: 'www.youtube.com',
        publishedAt: '2026-06-16T00:00:00Z',
        metricLabel: 'query: 서울특별시 부동산 시장 분석 토론 집코노미',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-youtube-listing',
        sourceId: 'serpapi:google_news',
        contentType: 'video',
        title: '[보증금 1억/월세 300만] 정선아리랑시장 인접 매물',
        snippet: '매물 홍보 영상입니다.',
        url: 'https://www.youtube.com/watch?v=listing',
        domain: 'www.youtube.com',
        publishedAt: '2026-06-16T00:00:00Z',
        metricLabel: 'query: 강원도 정선군 부동산 시장 분석 토론',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-youtube-hashtag',
        sourceId: 'serpapi:google_news',
        contentType: 'video',
        title: '경기도부동산',
        snippet: '집값전망 영상 모음입니다.',
        url: 'https://www.youtube.com/hashtag/demo',
        domain: 'www.youtube.com',
        publishedAt: '2026-06-16T00:00:00Z',
        metricLabel: 'query: 경기도 유튜브 부동산',
        statusLabel: 'search_candidate'
      }
    ]);

    expect(rows.map((row) => row.id)).toEqual(['serpapi-youtube-analysis']);
    expect(rows[0].category).toBe('videos');
  });

  it('keeps backend link candidates in the blog and community feed', () => {
    const rows = buildNewsroomFeedItems([
      {
        contentId: 'serpapi-link-community-roundup',
        sourceId: 'serpapi:google_news',
        contentType: 'link',
        title: 'community roundup for a hot apartment complex',
        snippet: 'public blog and community reaction candidate',
        url: 'https://allbareunhouse.com/post/demo',
        domain: 'allbareunhouse.com',
        metricLabel: 'query: real estate community',
        statusLabel: 'search_candidate'
      }
    ]);

    expect(rows).toHaveLength(1);
    expect(rows[0].category).toBe('links');
  });

  it('drops undated blog candidates that clearly point to old posts', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-06-17T00:00:00Z'));

    const rows = buildNewsroomFeedItems([
      {
        contentId: 'serpapi-link-old-blog',
        sourceId: 'serpapi:google_news',
        contentType: 'link',
        title: '2024년 07월 부산 부동산 블로그 글',
        snippet: '발행일시 : 7/16/2024',
        url: 'https://blog.naver.com/demo/old',
        domain: 'blog.naver.com',
        metricLabel: 'query: real estate blog',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-link-current-plan',
        sourceId: 'serpapi:google_news',
        contentType: 'link',
        title: '2026년 평택 부동산 개발 호재 정리',
        snippet: 'current year candidate',
        url: 'https://blog.naver.com/demo/current',
        domain: 'blog.naver.com',
        metricLabel: 'query: real estate blog',
        statusLabel: 'search_candidate'
      }
    ]);

    expect(rows.map((row) => row.id)).toEqual(['serpapi-link-current-plan']);
  });

  it('drops dated search candidates from a previous year', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-06-17T00:00:00Z'));

    const rows = buildNewsroomFeedItems([
      {
        contentId: 'serpapi-link-last-year-blog',
        sourceId: 'serpapi:google_news',
        contentType: 'link',
        title: '강남 아파트 재건축 블로그 분석',
        snippet: '부동산 시장과 단지 흐름을 정리한 글입니다.',
        url: 'https://blog.naver.com/demo/last-year',
        domain: 'blog.naver.com',
        publishedAt: '2025-12-20T00:00:00Z',
        metricLabel: 'query: 강남구 아파트 부동산 시장 블로그',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-link-fresh-blog',
        sourceId: 'serpapi:google_news',
        contentType: 'link',
        title: '강남 아파트 전세 흐름 블로그 분석',
        snippet: '최근 부동산 시장과 단지 반응을 정리한 글입니다.',
        url: 'https://blog.naver.com/demo/fresh',
        domain: 'blog.naver.com',
        publishedAt: '2026-06-12T00:00:00Z',
        metricLabel: 'query: 강남구 아파트 부동산 시장 블로그',
        statusLabel: 'search_candidate'
      }
    ]);

    expect(rows.map((row) => row.id)).toEqual(['serpapi-link-fresh-blog']);
  });

  it('drops low-quality local listing or lifestyle blog candidates', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-06-17T00:00:00Z'));

    const rows = buildNewsroomFeedItems([
      {
        contentId: 'serpapi-link-factory-auction',
        sourceId: 'serpapi:google_news',
        contentType: 'link',
        title: '부산시 공장 경매 사하구 일반공장 경매',
        snippet: '경매 물건 홍보 글입니다.',
        url: 'https://reyauction01.tistory.com/demo',
        domain: 'reyauction01.tistory.com',
        publishedAt: '2026-06-16T00:00:00Z',
        metricLabel: 'query: 부산 아파트 부동산 시장 블로그',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-link-apartment-analysis',
        sourceId: 'serpapi:google_news',
        contentType: 'link',
        title: '부산 아파트 전세와 매매가 흐름 블로그',
        snippet: '부동산 시장과 단지 가격 흐름을 정리했습니다.',
        url: 'https://blog.naver.com/demo/busan-apartment',
        domain: 'blog.naver.com',
        publishedAt: '2026-06-16T00:00:00Z',
        metricLabel: 'query: 부산 아파트 부동산 시장 블로그',
        statusLabel: 'search_candidate'
      }
    ]);

    expect(rows.map((row) => row.id)).toEqual(['serpapi-link-apartment-analysis']);
  });

  it('drops search results that do not match the requested content intent', () => {
    const rows = buildNewsroomFeedItems([
      {
        contentId: 'serpapi-video-from-blog-query',
        sourceId: 'serpapi:google_news',
        contentType: 'video',
        title: '강남 아파트 시장 해설 영상',
        snippet: '부동산 시장 영상입니다.',
        url: 'https://www.youtube.com/watch?v=demo',
        domain: 'www.youtube.com',
        publishedAt: '2026-06-16T00:00:00Z',
        metricLabel: 'query: 강남구 아파트 부동산 시장 블로그',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-blog-from-blog-query',
        sourceId: 'serpapi:google_news',
        contentType: 'link',
        title: '강남 아파트 시장 블로그 분석',
        snippet: '부동산 시장과 단지 흐름을 정리한 글입니다.',
        url: 'https://blog.naver.com/demo/blog',
        domain: 'blog.naver.com',
        publishedAt: '2026-06-16T00:00:00Z',
        metricLabel: 'query: 강남구 아파트 부동산 시장 블로그',
        statusLabel: 'search_candidate'
      }
    ]);

    expect(rows.map((row) => row.id)).toEqual(['serpapi-blog-from-blog-query']);
  });

  it('drops search candidates without real estate context in the result text', () => {
    const rows = buildNewsroomFeedItems([
      {
        contentId: 'serpapi-news-off-topic',
        sourceId: 'serpapi:google_news',
        contentType: 'news',
        title: '평택시 환경교육계획 공청회 개최',
        snippet: '교육 계획 수립을 위한 일반 공청회입니다.',
        url: 'https://example.com/off-topic',
        domain: 'example.com',
        metricLabel: 'query: 평택 부동산',
        statusLabel: 'search_candidate'
      },
      {
        contentId: 'serpapi-news-relevant',
        sourceId: 'serpapi:google_news',
        contentType: 'news',
        title: '평택 아파트 공급 계획 점검',
        snippet: '부동산 시장 관련 기사입니다.',
        url: 'https://example.com/relevant',
        domain: 'example.com',
        metricLabel: 'query: 평택 부동산',
        statusLabel: 'search_candidate'
      }
    ]);

    expect(rows.map((row) => row.id)).toEqual(['serpapi-news-relevant']);
  });
});
