export type RealEstateTargetSearchResult = {
  targetId: string;
  targetType: string;
  displayName: string;
};

type Fetcher = (input: string) => Promise<Response>;

/**
 * 단지명/지역명 문자열만으로 targetId를 찾는다 (커뮤니티 반응/뉴스/정책 타임라인 조회용).
 * 검색 결과가 여러 개면 단지(complex) 타입을 우선한다. 매칭 실패 시 null.
 */
export async function fetchRealEstateTargetIdByName(
  name: string,
  fetcher: Fetcher = fetch
): Promise<string | null> {
  const query = name.trim();
  if (!query) return null;

  const params = new URLSearchParams({ q: query, limit: '5' });
  const response = await fetcher(`/api/realestate/targets/search?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`real-estate target search request failed: ${response.status}`);
  }

  const payload = await response.json() as { items?: RealEstateTargetSearchResult[] };
  const items = Array.isArray(payload.items) ? payload.items : [];
  if (!items.length) return null;

  const complexMatch = items.find((item) => item.targetType === 'complex');
  return (complexMatch ?? items[0]).targetId;
}
