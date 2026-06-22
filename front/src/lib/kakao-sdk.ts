// Shared Kakao Maps SDK loader. Loads the SDK once with the `services` library so
// both map rendering (KakaoComplexMap) and geocoding (kakao-geocode) can reuse it.

export function isKakaoMapEnabled(): boolean {
  const isTestMode = import.meta.env.MODE === 'test';
  return import.meta.env.VITE_KAKAO_MAP_ENABLED === 'true' && !isTestMode;
}

export function kakaoJsKey(): string {
  return String(import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY ?? '').trim();
}

export async function loadKakaoSdk(appKey: string): Promise<void> {
  const globalWindow = window as any;

  // Already fully loaded with the services library.
  if (globalWindow.kakao?.maps?.services) {
    await new Promise<void>((resolve) => globalWindow.kakao.maps.load(resolve));
    return;
  }

  const existingPromise = globalWindow.__ybfKakaoSdkPromise as Promise<void> | undefined;
  if (existingPromise) {
    await existingPromise;
    return;
  }

  // Always (re)load the SDK script with the services library. If a previous load
  // pulled the core SDK without services, appending this script re-runs the loader
  // and registers services so geocoding works.
  globalWindow.__ybfKakaoSdkPromise = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script');
    script.dataset.ybfKakaoMap = 'true';
    script.async = true;
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(appKey)}&autoload=false&libraries=services`;
    script.addEventListener('load', () => globalWindow.kakao.maps.load(() => resolve()), { once: true });
    script.addEventListener('error', () => reject(new Error('Kakao map SDK failed to load')), { once: true });
    document.head.appendChild(script);
  });

  await globalWindow.__ybfKakaoSdkPromise;
}
