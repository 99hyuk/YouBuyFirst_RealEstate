export type NewsroomFilter = 'all' | 'news' | 'reports' | 'videos' | 'links';
export type NewsroomCategory = Exclude<NewsroomFilter, 'all'>;
export type NewsroomTone = 'news' | 'report' | 'video' | 'link';

export type RealEstateContentItem = {
  contentId: string;
  sourceId?: string | null;
  contentType?: string | null;
  title: string;
  snippet?: string | null;
  url: string;
  domain?: string | null;
  publishedAt?: string | null;
  metricLabel?: string | null;
  statusLabel?: string | null;
  ingestedAt?: string | null;
  dataStatus?: string | null;
  targetId?: string | null;
  linkType?: string | null;
  confidence?: number | null;
  reviewState?: string | null;
};

export type NewsroomFeedItem = {
  id: string;
  category: NewsroomCategory;
  tone: NewsroomTone;
  title: string;
  source: string;
  iconDomain: string;
  iconClass: string;
  url: string;
  meta: string;
  statusLabel: string;
  rankLabel?: string;
};

export type FetchRealEstateNewsroomParams = {
  feed?: NewsroomFilter;
  page?: number;
  pageSize?: number;
};

export type FetchRealEstateTargetContentParams = {
  feed?: NewsroomFilter;
  limit?: number;
};

type Fetcher = (input: string) => Promise<Response>;

export async function fetchRealEstateNewsroom(
  params: FetchRealEstateNewsroomParams = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateContentItem[]> {
  const query = new URLSearchParams();
  query.set('feed', apiFeed(params.feed ?? 'all'));
  query.set('page', String(params.page ?? 1));
  query.set('pageSize', String(params.pageSize ?? 15));

  const response = await fetcher(`/api/realestate/newsroom?${query.toString()}`);
  if (!response.ok) {
    throw new Error(`real-estate newsroom request failed: ${response.status}`);
  }
  const payload = await response.json() as { items?: RealEstateContentItem[] };
  return Array.isArray(payload.items) ? payload.items : [];
}

export async function fetchRealEstateTargetContent(
  targetId: string,
  params: FetchRealEstateTargetContentParams = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateContentItem[]> {
  const query = new URLSearchParams();
  query.set('feed', apiFeed(params.feed ?? 'all'));
  query.set('limit', String(params.limit ?? 50));

  const response = await fetcher(`/api/realestate/targets/${encodeURIComponent(targetId)}/content?${query.toString()}`);
  if (!response.ok) {
    throw new Error(`real-estate target content request failed: ${response.status}`);
  }
  const payload = await response.json() as { items?: RealEstateContentItem[] };
  return Array.isArray(payload.items) ? payload.items : [];
}

export function buildNewsroomFeedItems(items: RealEstateContentItem[]): NewsroomFeedItem[] {
  const rankCounters: Record<'videos' | 'links', number> = {
    videos: 0,
    links: 0
  };

  return items.map((item) => {
    const category = contentCategory(item.contentType);
    const tone = contentTone(category);
    const iconDomain = item.domain ?? hostname(item.url);
    const rankLabel = category === 'videos' || category === 'links'
      ? `${++rankCounters[category]}위`
      : undefined;

    return {
      id: item.contentId,
      category,
      tone,
      title: item.title,
      source: sourceLabel(item.sourceId, iconDomain),
      iconDomain,
      iconClass: contentIconClass(item.contentType, iconDomain),
      url: item.url,
      meta: contentMeta(item),
      statusLabel: displayStatusLabel(item),
      ...(rankLabel ? { rankLabel } : {})
    };
  });
}

function apiFeed(feed: NewsroomFilter): string {
  const map: Record<NewsroomFilter, string> = {
    all: 'all',
    news: 'news',
    reports: 'report',
    videos: 'video',
    links: 'link'
  };
  return map[feed] ?? 'all';
}

function contentCategory(contentType?: string | null): NewsroomCategory {
  const normalized = (contentType ?? '').toLowerCase();
  if (['report', 'reports', 'column', 'official_notice'].includes(normalized)) return 'reports';
  if (['video', 'videos', 'youtube'].includes(normalized)) return 'videos';
  if (['link', 'links', 'blog', 'community'].includes(normalized)) return 'links';
  return 'news';
}

function contentTone(category: NewsroomCategory): NewsroomTone {
  if (category === 'reports') return 'report';
  if (category === 'videos') return 'video';
  if (category === 'links') return 'link';
  return 'news';
}

function contentIconClass(contentType?: string | null, domain = ''): string {
  const normalizedType = (contentType ?? '').toLowerCase();
  const normalizedDomain = domain.toLowerCase();
  if (normalizedDomain.includes('youtube') || normalizedType === 'video') return 'youtube';
  if (normalizedDomain === 'blog.naver.com') return 'naver-blog';
  if (normalizedDomain === 'cafe.naver.com') return 'naver';
  if (normalizedDomain === 'cafe.daum.net') return 'community';
  if (['report', 'column', 'official_notice'].includes(normalizedType)) return 'news-research';
  if (['link', 'blog', 'community'].includes(normalizedType)) return 'community';
  return 'news';
}

function contentMeta(item: RealEstateContentItem): string {
  const dateLabel = dateOnly(item.publishedAt) ?? dateOnly(item.ingestedAt) ?? '발행일 확인 필요';
  const metric = trimToNull(item.metricLabel);
  return metric ? `${dateLabel} · ${metric}` : dateLabel;
}

function displayStatusLabel(item: RealEstateContentItem): string {
  const statusLabel = trimToNull(item.statusLabel);
  if (statusLabel) return statusLabel;

  const dataStatus = (item.dataStatus ?? '').toLowerCase();
  if (dataStatus === 'ok') return '수집 확인';
  if (dataStatus === 'mock') return 'mock';
  if (dataStatus === 'stale') return '지연 가능';
  if (dataStatus === 'empty') return '데이터 없음';
  return '확인 필요';
}

function sourceLabel(sourceId?: string | null, domain = ''): string {
  const normalized = (sourceId ?? '').toLowerCase();
  const map: Record<string, string> = {
    data_go_kr: '공공데이터포털',
    ddangzipgo: '땅집고',
    molit: '국토교통부',
    naver_blog: '네이버 블로그',
    naver_cafe: '네이버 카페',
    reb: '한국부동산원',
    youtube: '유튜브'
  };
  if (map[normalized]) return map[normalized];
  if (domain) return domain;
  return '출처 확인 필요';
}

function hostname(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return '';
  }
}

function dateOnly(value?: string | null): string | null {
  const trimmed = trimToNull(value);
  if (!trimmed) return null;
  return trimmed.slice(0, 10);
}

function trimToNull(value?: string | null): string | null {
  if (value === null || value === undefined || value.trim() === '') return null;
  return value.trim();
}
