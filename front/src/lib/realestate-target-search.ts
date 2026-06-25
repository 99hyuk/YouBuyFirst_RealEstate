import { repairMojibake } from './text-encoding';

export type RealEstateTargetSearchResult = {
  targetId: string;
  targetType: string;
  displayName: string;
  slug?: string | null;
  reviewState?: string | null;
  dataStatus?: string | null;
  regionLevel?: string | null;
  parentTargetId?: string | null;
  legalDongCode?: string | null;
  regionCode?: string | null;
};

export type FetchRealEstateTargetSuggestionsParams = {
  limit?: number;
};

type Fetcher = (input: string) => Promise<Response>;

export const MIN_TARGET_SEARCH_LENGTH = 2;
export const TARGET_SEARCH_LIMIT = 8;

export function normalizeTargetSearchText(value: string): string {
  return value.trim().replace(/[^\p{L}\p{N}]/gu, '');
}

export async function fetchRealEstateTargetSuggestions(
  query: string,
  params: FetchRealEstateTargetSuggestionsParams = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateTargetSearchResult[]> {
  const trimmed = query.trim();
  if (normalizeTargetSearchText(trimmed).length < MIN_TARGET_SEARCH_LENGTH) {
    return [];
  }

  const search = new URLSearchParams();
  search.set('q', trimmed);
  search.set('limit', String(params.limit ?? TARGET_SEARCH_LIMIT));
  search.set('mode', 'autocomplete');

  const response = await fetcher(`/api/realestate/targets/search?${search.toString()}`);
  if (!response.ok) {
    throw new Error(`target search request failed: ${response.status}`);
  }

  const payload = await response.json() as { items?: RealEstateTargetSearchResult[] };
  return Array.isArray(payload.items) ? payload.items.map(normalizeTargetSearchResult) : [];
}

function normalizeTargetSearchResult(item: RealEstateTargetSearchResult): RealEstateTargetSearchResult {
  return {
    targetId: item.targetId,
    targetType: repairMojibake(item.targetType) || 'region',
    displayName: repairMojibake(item.displayName) || item.targetId,
    slug: repairMojibake(item.slug),
    reviewState: repairMojibake(item.reviewState),
    dataStatus: repairMojibake(item.dataStatus),
    regionLevel: repairMojibake(item.regionLevel),
    parentTargetId: repairMojibake(item.parentTargetId),
    legalDongCode: repairMojibake(item.legalDongCode),
    regionCode: repairMojibake(item.regionCode)
  };
}
