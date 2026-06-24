export type ScheduleTone = 'market' | 'deal' | 'supply' | 'finance' | 'policy' | 'subscription';

export type MarketDataScheduleEvent = {
  id: string;
  date: string;
  title: string;
  category: string;
  source: string;
  summary: string;
  link: string;
  tone: ScheduleTone;
  provider?: string | null;
  status?: string | null;
  dataStatus?: string | null;
  stale?: boolean | null;
  lastCheckedAt?: string | null;
  asOf?: string | null;
};

export type MarketDataSourceLink = {
  id: string;
  title: string;
  label: string;
  link: string;
  provider?: string | null;
  status?: string | null;
  stale?: boolean | null;
  lastCheckedAt?: string | null;
};

export type MarketDataScheduleResponse = {
  month: string;
  scheduleEvents: MarketDataScheduleEvent[];
  sourceLinks: MarketDataSourceLink[];
};

export type FetchMarketDataSchedulesParams = {
  month?: string;
};

type Fetcher = (input: string) => Promise<Response>;

export async function fetchMarketDataSchedules(
  params: FetchMarketDataSchedulesParams = {},
  fetcher: Fetcher = fetch
): Promise<MarketDataScheduleResponse> {
  const query = new URLSearchParams();
  if (params.month) {
    query.set('month', params.month);
  }
  const suffix = query.toString() ? `?${query.toString()}` : '';
  const response = await fetcher(`/api/realestate/market-data-schedules${suffix}`);
  if (!response.ok) {
    throw new Error(`real-estate market-data schedules request failed: ${response.status}`);
  }
  const payload = await response.json() as Partial<MarketDataScheduleResponse>;
  return {
    month: typeof payload.month === 'string' ? payload.month : params.month ?? currentMonth(),
    scheduleEvents: Array.isArray(payload.scheduleEvents) ? payload.scheduleEvents.map(normalizeScheduleEvent) : [],
    sourceLinks: Array.isArray(payload.sourceLinks) ? payload.sourceLinks.map(normalizeSourceLink) : []
  };
}

export function currentMonth(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
}

function normalizeScheduleEvent(event: MarketDataScheduleEvent): MarketDataScheduleEvent {
  return {
    ...event,
    id: String(event.id),
    date: String(event.date),
    title: String(event.title),
    category: String(event.category),
    source: String(event.source),
    summary: String(event.summary ?? ''),
    link: String(event.link),
    tone: normalizeTone(event.tone)
  };
}

function normalizeSourceLink(source: MarketDataSourceLink): MarketDataSourceLink {
  return {
    ...source,
    id: String(source.id),
    title: String(source.title),
    label: String(source.label),
    link: String(source.link)
  };
}

function normalizeTone(value: string): ScheduleTone {
  if (['market', 'deal', 'supply', 'finance', 'policy', 'subscription'].includes(value)) {
    return value as ScheduleTone;
  }
  return 'market';
}
