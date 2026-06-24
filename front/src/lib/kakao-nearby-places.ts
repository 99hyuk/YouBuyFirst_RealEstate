import { isKakaoMapEnabled, kakaoJsKey, loadKakaoSdk } from './kakao-sdk';

export type NearbyFacility = { name: string; distanceMeters: number };
export type NearbyFacilities = {
  subway: NearbyFacility | null;
  bus: NearbyFacility | null;
  store: NearbyFacility | null;
};

const SEARCH_RADIUS_METERS = 1000;

function nearestResult(data: any[], status: string, kakao: any): NearbyFacility | null {
  if (status !== kakao.maps.services.Status.OK || !data.length) return null;
  const nearest = data[0];
  return { name: nearest.place_name, distanceMeters: Number(nearest.distance) };
}

function searchByCategory(places: any, kakao: any, code: string, location: any): Promise<NearbyFacility | null> {
  return new Promise((resolve) => {
    places.categorySearch(
      code,
      (data: any[], status: string) => resolve(nearestResult(data, status, kakao)),
      { location, radius: SEARCH_RADIUS_METERS, sort: kakao.maps.services.SortBy.DISTANCE }
    );
  });
}

function searchByKeyword(places: any, kakao: any, keyword: string, location: any): Promise<NearbyFacility | null> {
  return new Promise((resolve) => {
    places.keywordSearch(
      keyword,
      (data: any[], status: string) => resolve(nearestResult(data, status, kakao)),
      { location, radius: SEARCH_RADIUS_METERS, sort: kakao.maps.services.SortBy.DISTANCE }
    );
  });
}

/**
 * 선택 좌표 1km 이내 지하철역(SW8)/버스정류장(키워드 검색)/편의점·마트(CS2) 중
 * 가장 가까운 곳을 찾는다. 카카오 지도 SDK가 비활성/로드 실패하면 null.
 */
export async function fetchNearbyFacilities(center: { lat: number; lng: number }): Promise<NearbyFacilities | null> {
  if (!isKakaoMapEnabled()) return null;
  const appKey = kakaoJsKey();
  if (!appKey) return null;

  try {
    await loadKakaoSdk(appKey);
    const kakao = (window as any).kakao;
    if (!kakao?.maps?.services) return null;

    const places = new kakao.maps.services.Places();
    const location = new kakao.maps.LatLng(center.lat, center.lng);

    const [subway, bus, store] = await Promise.all([
      searchByCategory(places, kakao, 'SW8', location),
      searchByKeyword(places, kakao, '버스정류장', location),
      searchByCategory(places, kakao, 'CS2', location)
    ]);

    return { subway, bus, store };
  } catch {
    return null;
  }
}
