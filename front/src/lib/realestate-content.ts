import { repairMojibake } from './text-encoding';

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
  derived?: boolean;
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
const SEARCH_CANDIDATE_MAX_AGE_DAYS = 90;
const DAY_MS = 24 * 60 * 60 * 1000;

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
  return items.flatMap((item) => {
    const normalizedItem = normalizeContentItem(item);
    if (!shouldDisplayContentItem(normalizedItem)) return [];

    const category = contentCategory(normalizedItem);
    const tone = contentTone(category);
    const iconDomain = normalizedItem.domain ?? hostname(normalizedItem.url);

    return [{
      id: normalizedItem.contentId,
      category,
      tone,
      title: normalizedItem.title,
      source: sourceLabel(normalizedItem.sourceId, iconDomain),
      iconDomain,
      iconClass: contentIconClass(normalizedItem.contentType, iconDomain, normalizedItem.title, category),
      url: normalizedItem.url,
      meta: contentMeta(normalizedItem),
      statusLabel: displayStatusLabel(normalizedItem)
    }];
  });
}

export function ensureNewsroomCategoryCoverage(items: NewsroomFeedItem[]): NewsroomFeedItem[] {
  return items;
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

function normalizeContentItem(item: RealEstateContentItem): RealEstateContentItem {
  return {
    ...item,
    title: repairMojibake(item.title),
    snippet: repairMojibake(item.snippet),
    metricLabel: repairMojibake(item.metricLabel),
    statusLabel: repairMojibake(item.statusLabel),
    domain: repairMojibake(item.domain),
    sourceId: repairMojibake(item.sourceId)
  };
}

function contentCategory(item: RealEstateContentItem): NewsroomCategory {
  const normalized = (item.contentType ?? '').toLowerCase();
  const domain = (item.domain ?? hostname(item.url)).toLowerCase();
  const searchable = `${item.title} ${item.snippet ?? ''} ${item.metricLabel ?? ''} ${domain}`.toLowerCase();
  const isSearchCandidate = isSearchCandidateItem(item);

  if (['video', 'videos', 'youtube'].includes(normalized)) {
    return !isSearchCandidate || isVideoDomain(domain) ? 'videos' : 'news';
  }
  if (['link', 'links', 'blog', 'community'].includes(normalized)) {
    return 'links';
  }
  if (['report', 'reports', 'column', 'official_notice'].includes(normalized)) {
    return !isSearchCandidate || isReportDomain(domain) ? 'reports' : 'news';
  }
  if (normalized === 'news' && !isSearchCandidate) return 'news';
  if (isVideoDomain(domain)) return 'videos';
  if (isLinkDomain(domain)) return 'links';
  if (isReportDomain(domain) || (!isSearchCandidate && isReportLikeText(searchable))) return 'reports';
  if (!isSearchCandidate && /동영상|영상|유튜브|영상 브리핑|브리핑 영상|인터뷰 영상/.test(searchable)) return 'videos';
  if (!isSearchCandidate && /칼럼|블로그|브런치|커뮤니티|카페 글|원문 후기/.test(searchable)) return 'links';
  return 'news';
}

function shouldDisplayContentItem(item: RealEstateContentItem): boolean {
  if (!isSearchCandidateItem(item)) return true;

  const domain = (item.domain ?? hostname(item.url)).toLowerCase();
  const searchable = `${item.title} ${item.snippet ?? ''} ${domain}`.toLowerCase();

  if (isJobDomain(domain)) return false;
  if (domain === 'gogogogo.kr' && /\/share\/youtube\//.test(item.url)) return false;
  if (isMismatchedSearchIntent(item, domain)) return false;
  if (!hasRealEstateContentSignal(searchable)) return false;
  if (isVideoDomain(domain) && (isInvalidYouTubeCandidateUrl(item.url) || !trustedRealEstateVideoSignal(searchable))) return false;
  if (isStaleSearchCandidate(item, searchable, domain)) return false;
  if (isLowQualityRealEstateSearchCandidate(searchable, domain)) return false;
  if (/채용|구인|구직|recruit|jobkorea|saramin|wanted/.test(searchable)) return false;
  return true;
}

function isSearchCandidateItem(item: RealEstateContentItem): boolean {
  const sourceId = (item.sourceId ?? '').toLowerCase();
  const dataStatus = (item.dataStatus ?? '').toLowerCase();
  const statusLabel = (item.statusLabel ?? '').toLowerCase();
  return sourceId === 'serpapi:google_news'
    || dataStatus === 'candidate'
    || statusLabel === 'search_candidate';
}

function isStaleSearchCandidate(item: RealEstateContentItem, searchable: string, domain: string): boolean {
  const normalized = (item.contentType ?? '').toLowerCase();
  const isLinkCandidate = ['link', 'links', 'blog', 'community'].includes(normalized) || isLinkDomain(domain);

  const publishedAt = parseTimestamp(item.publishedAt);
  if (publishedAt) {
    const now = new Date();
    const ageDays = Math.floor((now.getTime() - publishedAt.getTime()) / DAY_MS);
    if (publishedAt.getUTCFullYear() < now.getUTCFullYear()) return true;
    return ageDays > SEARCH_CANDIDATE_MAX_AGE_DAYS;
  }

  const years = yearHints(searchable);
  if (!years.length) return false;

  const currentYear = new Date().getUTCFullYear();
  const hasPastYear = years.some((year) => year < currentYear);
  const hasCurrentOrFutureYear = years.some((year) => year >= currentYear);
  return isLinkCandidate && hasPastYear && !hasCurrentOrFutureYear;
}

function parseTimestamp(value?: string | null): Date | null {
  if (!value) return null;
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return null;
  return new Date(timestamp);
}

function isMismatchedSearchIntent(item: RealEstateContentItem, domain: string): boolean {
  const query = `${item.metricLabel ?? ''}`.toLowerCase();
  if (!query.includes('query:')) return false;
  if (query.includes('블로그') && !isLinkDomain(domain)) return true;
  if ((query.includes('영상') || query.includes('유튜브')) && !isVideoDomain(domain)) return true;
  if (query.includes('리포트') && !(isReportDomain(domain) || isReportLikeText(`${item.title} ${item.snippet ?? ''}`.toLowerCase()))) {
    return true;
  }
  return false;
}

function trustedRealEstateVideoSignal(searchable: string): boolean {
  return /부읽남|부동산\s*읽어주는\s*남자|집코노미|매부리tv|삼프로tv|3protv|김작가\s*tv|스튜tv|스마트튜브|빠숑|kb부동산tv|부동산r114|직방tv|땅집고/.test(searchable);
}

function isInvalidYouTubeCandidateUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    const hostname = parsed.hostname.toLowerCase();
    if (!isVideoDomain(hostname)) return false;
    if (hostname === 'youtu.be') return false;
    return !parsed.pathname.startsWith('/watch');
  } catch {
    return true;
  }
}

function isLowQualityRealEstateSearchCandidate(searchable: string, domain: string): boolean {
  const isMediaOrLink = isLinkDomain(domain) || isVideoDomain(domain);
  if (!isMediaOrLink) return false;
  return /속눈썹|펜션|캠핑|맛집|전통시장|체험단|원룸텔|고시원|일반공장|경매|법원입찰|급매매\s*추천|매물\s*홍보|소액으로|보증금\s*\d|월세\s*\d|논\s*밭|임야|전원생활|토지매매|no:\s*|아늑한|전원주택|단독주택|상가\s*매매|하이엔드\s*타운하우스|언박싱/.test(searchable);
}

function hasRealEstateContentSignal(value: string): boolean {
  return /부동산|아파트|주택|주거|전세|월세|전월세|매매가|매매\s*가격|분양|청약|재건축|재개발|입주|공시가격|실거래|대출|금리|학군|교통|개발|공급|집값|시세|단지|real estate|housing|apartment/.test(value);
}

function yearHints(value: string): number[] {
  const years = new Set<number>();
  for (const match of value.matchAll(/20\d{2}/g)) {
    years.add(Number(match[0]));
  }
  for (const match of value.matchAll(/(?:^|[^\d])(\d{2})\s*년/g)) {
    const year = Number(match[1]);
    if (year >= 0 && year <= 99) {
      years.add(2000 + year);
    }
  }
  return [...years];
}

function contentTone(category: NewsroomCategory): NewsroomTone {
  if (category === 'reports') return 'report';
  if (category === 'videos') return 'video';
  if (category === 'links') return 'link';
  return 'news';
}

function contentIconClass(
  contentType?: string | null,
  domain = '',
  title = '',
  category: NewsroomCategory = 'news'
): string {
  const normalizedType = (contentType ?? '').toLowerCase();
  const normalizedDomain = domain.toLowerCase();
  const normalizedTitle = title.toLowerCase();
  if (category === 'videos' && (normalizedDomain.includes('youtube') || normalizedType === 'video')) return 'youtube';
  if (normalizedDomain === 'blog.naver.com') return 'naver-blog';
  if (normalizedDomain === 'cafe.naver.com') return 'naver';
  if (normalizedDomain === 'cafe.daum.net') return 'community';
  if (normalizedDomain.includes('brunch') || normalizedDomain.includes('blog') || normalizedDomain.includes('tistory')) return 'naver-blog';
  if (isReportDomain(normalizedDomain) || /보고서|리포트|연구원|리서치|전망/.test(normalizedTitle)) return 'news-research';
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
  if (statusLabel) return displayRawStatusLabel(statusLabel);

  const dataStatus = (item.dataStatus ?? '').toLowerCase();
  if (dataStatus === 'ok') return '수집 확인';
  if (dataStatus === 'mock') return '수집 전/insufficient';
  if (dataStatus === 'insufficient') return '수집 전/insufficient';
  if (dataStatus === 'stale') return '지연 가능';
  if (dataStatus === 'empty') return '데이터 없음';
  return '확인 필요';
}

function sourceLabel(sourceId?: string | null, domain = ''): string {
  const normalized = (sourceId ?? '').toLowerCase();
  const map: Record<string, string> = {
    data_go_kr: '공공데이터포털',
    ddangzipgo: '땅집고',
    expert_report_search: '전문 리포트 검색',
    google_news_blog_search: '최근 블로그 검색',
    google_news_rss: 'Google 뉴스',
    kbthink_column_search: 'KB Think 컬럼',
    'naver_blog:building-standard': '빌딩의 정석',
    'naver_blog:ppassong': '빠숑의 세상 답사기',
    molit: '국토교통부',
    naver_blog: '네이버 블로그',
    naver_cafe: '네이버 카페',
    reb: '한국부동산원',
    'report:hf-kif': 'HF·KIF 연구자료',
    'report:hanaif': '하나금융연구소',
    'report:kb-research': 'KB금융 리서치',
    'report:official-research': '공공·연구기관 리포트',
    'report:wfri': '우리금융경영연구소',
    'serpapi:google_news': '최근 이슈 검색',
    'tistory:auctionguide': 'Tistory 시장분석',
    'tistory:news8253': '동동이의 트렌드 앞서가기',
    youtube: '유튜브',
    'youtube:3protv': '삼프로TV',
    'youtube:buiknam': '부읽남TV',
    'youtube:butv': '부티비',
    'youtube:jipconomy': '집코노미',
    'youtube:kimjagga': '김작가TV',
    'youtube:smarttube': '스마트튜브',
    'youtube:maeburitv': '매부리TV'
  };
  if (normalized === 'serpapi:google_news' && domain) {
    return domainLabel(domain);
  }
  if (map[normalized]) return map[normalized];
  if (domain) return domainLabel(domain);
  return '출처 확인 필요';
}

function isReportDomain(domain: string): boolean {
  return [
    'www.reb.or.kr',
    'www.molit.go.kr',
    'www.krihs.re.kr',
    'kremap.krihs.re.kr',
    'www.cerik.re.kr',
    'cerik.re.kr',
    'www.kab.co.kr',
    'www.khug.or.kr',
    'www.hf.go.kr',
    'www.bok.or.kr',
    'www.fss.or.kr',
    'www.kdi.re.kr',
    'www.kbfg.com',
    'www.kbstar.com',
    'kbthink.com',
    'hanaif.re.kr',
    'www.hanaif.re.kr',
    'wfri.re.kr',
    'www.wfri.re.kr',
    'researcher.hf.go.kr',
    'kif.re.kr',
    'www.kif.re.kr',
    'www.hanafn.com',
    'www.shinhan.com',
    'www.woorifg.com',
    'www.nhwm.com',
    'www.miraeasset.com',
    'securities.miraeasset.com',
    'www.samsungpop.com'
  ].includes(domain);
}

function isVideoDomain(domain: string): boolean {
  return /youtube|youtu\.be/.test(domain);
}

function isLinkDomain(domain: string): boolean {
  return /blog|brunch|tistory|cafe/.test(domain);
}

function isJobDomain(domain: string): boolean {
  return /jobkorea|saramin|wanted/.test(domain);
}

function isReportLikeText(searchable: string): boolean {
  return /보고서|리포트|연구원|리서치|전망 자료|시장 전망|월간 동향|주간 동향|주택 통계|가격지수 통계|k-hai/.test(searchable);
}

function displayRawStatusLabel(value: string): string {
  const normalized = value.trim().toLowerCase();
  if (normalized === 'search_candidate') return '근거 후보';
  if (normalized === 'candidate') return '후보';
  return value;
}

function domainLabel(domain: string): string {
  const normalized = domain.toLowerCase();
  const labels: Record<string, string> = {
    'www.youtube.com': '유튜브',
    'youtu.be': '유튜브',
    'blog.naver.com': '네이버 블로그',
    'auctionguide.tistory.com': 'Tistory 시장분석',
    'news8253.tistory.com': '동동이의 트렌드 앞서가기',
    'cafe.naver.com': '네이버 카페',
    'cafe.daum.net': '다음 카페',
    'v.daum.net': '다음 뉴스',
    'www.google.co.kr': 'Google 검색',
    'news.google.com': 'Google 뉴스',
    'www.hankyung.com': '한국경제',
    'magazine.hankyung.com': '한경 매거진',
    'www.mk.co.kr': '매일경제',
    'www.sedaily.com': '서울경제',
    'biz.chosun.com': '조선비즈',
    'realty.chosun.com': '땅집고',
    'www.yna.co.kr': '연합뉴스',
    'news.kbs.co.kr': 'KBS 뉴스',
    'www.reb.or.kr': '한국부동산원',
    'www.molit.go.kr': '국토교통부',
    'www.krihs.re.kr': '국토연구원',
    'kremap.krihs.re.kr': '국토연구원 부동산시장연구센터',
    'www.cerik.re.kr': '한국건설산업연구원',
    'cerik.re.kr': '한국건설산업연구원',
    'www.bok.or.kr': '한국은행',
    'www.khug.or.kr': 'HUG',
    'www.kbfg.com': 'KB금융',
    'www.kbstar.com': 'KB국민은행',
    'kbthink.com': 'KB Think',
    'hanaif.re.kr': '하나금융연구소',
    'www.hanaif.re.kr': '하나금융연구소',
    'wfri.re.kr': '우리금융경영연구소',
    'www.wfri.re.kr': '우리금융경영연구소',
    'researcher.hf.go.kr': '주택금융연구원',
    'kif.re.kr': '한국금융연구원',
    'www.kif.re.kr': '한국금융연구원',
    'www.shinhan.com': '신한은행',
    'www.woorifg.com': '우리금융',
    'www.nhwm.com': 'NH투자증권',
    'www.miraeasset.com': '미래에셋'
  };
  return labels[normalized] ?? domain;
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
