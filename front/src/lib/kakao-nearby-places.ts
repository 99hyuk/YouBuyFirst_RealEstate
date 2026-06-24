import { isKakaoMapEnabled, kakaoJsKey, loadKakaoSdk } from './kakao-sdk';

export type NearbyFacility = { name: string; distanceMeters: number; lat: number; lng: number };
export type NearbyFacilities = {
  subway: NearbyFacility | null;
  bus: NearbyFacility | null;
  store: NearbyFacility | null;
  school: NearbyFacility | null;
};

const SEARCH_RADIUS_METERS = 1000;

function nearestResult(data: any[], status: string, kakao: any): NearbyFacility | null {
  if (status !== kakao.maps.services.Status.OK || !data.length) return null;
  const nearest = data[0];
  return {
    name: nearest.place_name,
    distanceMeters: Number(nearest.distance),
    lat: Number(nearest.y),
    lng: Number(nearest.x)
  };
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
 * 선택 좌표 1km 이내 지하철역(SW8)/버스정류장(키워드 검색)/편의점·마트(CS2)/학교(SC4) 중
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

    const [subway, bus, store, school] = await Promise.all([
      searchByCategory(places, kakao, 'SW8', location),
      searchByKeyword(places, kakao, '버스정류장', location),
      searchByCategory(places, kakao, 'CS2', location),
      searchByCategory(places, kakao, 'SC4', location)
    ]);

    return { subway, bus, store, school };
  } catch {
    return null;
  }
}

export type KakaoMapDirectionsPoint = { name: string; lat: number; lng: number };

/**
 * 출발지(선택 단지)→도착지(주변 시설) 카카오맵 길찾기 페이지 링크.
 * 새 탭에서 열면 rt1(출발지)/rt2(도착지)가 모두 채워진 채로 실제 도보 경로/시간을 보여준다.
 */
export function kakaoMapDirectionsUrl(origin: KakaoMapDirectionsPoint, destination: KakaoMapDirectionsPoint): string {
  const from = `${encodeURIComponent(origin.name)},${origin.lat},${origin.lng}`;
  const to = `${encodeURIComponent(destination.name)},${destination.lat},${destination.lng}`;
  return `https://map.kakao.com/link/from/${from}/to/${to}`;
}
