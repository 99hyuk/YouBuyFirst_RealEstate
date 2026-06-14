export type RealEstateTimelineEvent = {
  id: string;
  targetId?: string | null;
  eventType?: string | null;
  sourceRefType?: string | null;
  sourceRefId?: string | null;
  title: string;
  summary?: string | null;
  occurredAt?: string | null;
  asOf?: string | null;
  dataStatus?: string | null;
};

export type FetchRealEstateTargetTimelineParams = {
  eventType?: string;
  limit?: number;
};

type Fetcher = (input: string) => Promise<Response>;

export async function fetchRealEstateTargetTimeline(
  targetId: string,
  params: FetchRealEstateTargetTimelineParams = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateTimelineEvent[]> {
  const query = new URLSearchParams();
  if (params.eventType) {
    query.set('eventType', params.eventType);
  }
  query.set('limit', String(params.limit ?? 20));

  const response = await fetcher(`/api/realestate/targets/${encodeURIComponent(targetId)}/timeline?${query.toString()}`);
  if (!response.ok) {
    throw new Error(`real-estate target timeline request failed: ${response.status}`);
  }

  const payload = await response.json() as { items?: RealEstateTimelineEvent[] };
  return Array.isArray(payload.items) ? payload.items : [];
}
