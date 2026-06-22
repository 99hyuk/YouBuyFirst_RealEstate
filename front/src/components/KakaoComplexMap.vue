<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

export type ComplexMapTone = 'up' | 'down' | 'flat';

export type ComplexMapMarker = {
  targetId: string;
  name: string;
  address: string;
  region: string;
  lat: number;
  lng: number;
  tone: ComplexMapTone;
  price: string;
  change: string;
  reaction: string;
  provider: string;
  asOf: string;
  dataStatus: string;
  note: string;
};

type MapCenter = {
  lat: number;
  lng: number;
};

const props = withDefaults(defineProps<{
  markers: ComplexMapMarker[];
  selectedTargetId?: string;
  center?: MapCenter;
  level?: number;
  markerSourceStatus?: string;
}>(), {
  selectedTargetId: '',
  level: 5,
  markerSourceStatus: ''
});

const emit = defineEmits<{
  select: [marker: ComplexMapMarker];
}>();

const mapContainer = ref<HTMLElement | null>(null);
const mapState = ref<'loading' | 'ready' | 'fallback' | 'error'>('loading');
const selectedMarkerId = ref(props.selectedTargetId);

let renderedMap: any = null;
let renderedMarkers: any[] = [];

const isTestMode = import.meta.env.MODE === 'test';
const kakaoEnabled = computed(() => import.meta.env.VITE_KAKAO_MAP_ENABLED === 'true' && !isTestMode);
const kakaoKey = computed(() => String(import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY ?? '').trim());
const canUseKakao = computed(() => kakaoEnabled.value && kakaoKey.value.length > 0);
const hasMarkers = computed(() => props.markers.length > 0);
const selectedMarker = computed(() => (
  props.markers.find((marker) => marker.targetId === selectedMarkerId.value) ?? props.markers[0] ?? null
));
const mapCenter = computed(() => props.center ?? selectedMarker.value ?? props.markers[0]);
const statusLabel = computed(() => {
  if (!hasMarkers.value) return 'marker 없음';
  if (mapState.value === 'ready') return 'kakao sdk';
  if (mapState.value === 'error') return '지도 SDK 대체 표시';
  if (!kakaoEnabled.value) return '지도 SDK 대기';
  if (!kakaoKey.value) return 'key missing';
  return 'loading';
});
const displayStatusLabel = computed(() => (
  props.markerSourceStatus ? `${statusLabel.value} · ${props.markerSourceStatus}` : statusLabel.value
));

const lngRange = computed(() => {
  const lngs = props.markers.map((marker) => marker.lng);
  return {
    min: Math.min(...lngs, mapCenter.value?.lng ?? 0) - 0.002,
    max: Math.max(...lngs, mapCenter.value?.lng ?? 0) + 0.002
  };
});

const latRange = computed(() => {
  const lats = props.markers.map((marker) => marker.lat);
  return {
    min: Math.min(...lats, mapCenter.value?.lat ?? 0) - 0.002,
    max: Math.max(...lats, mapCenter.value?.lat ?? 0) + 0.002
  };
});

const fallbackPointStyle = (marker: ComplexMapMarker) => {
  const xDenominator = Math.max(lngRange.value.max - lngRange.value.min, 0.0001);
  const yDenominator = Math.max(latRange.value.max - latRange.value.min, 0.0001);
  const left = ((marker.lng - lngRange.value.min) / xDenominator) * 100;
  const top = (1 - ((marker.lat - latRange.value.min) / yDenominator)) * 100;

  return {
    left: `${Math.min(Math.max(left, 8), 92)}%`,
    top: `${Math.min(Math.max(top, 12), 88)}%`
  };
};

const setSelectedMarker = (marker: ComplexMapMarker) => {
  selectedMarkerId.value = marker.targetId;
  emit('select', marker);
  focusKakaoMarker(marker);
};

const loadKakaoSdk = async () => {
  if ((window as any).kakao?.maps) {
    await new Promise<void>((resolve) => (window as any).kakao.maps.load(resolve));
    return;
  }

  const existingPromise = (window as any).__ybfKakaoMapPromise as Promise<void> | undefined;
  if (existingPromise) {
    await existingPromise;
    return;
  }

  (window as any).__ybfKakaoMapPromise = new Promise<void>((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>('script[data-ybf-kakao-map="true"]');
    if (existingScript) {
      existingScript.addEventListener('load', () => (window as any).kakao.maps.load(resolve), { once: true });
      existingScript.addEventListener('error', () => reject(new Error('Kakao map SDK failed to load')), { once: true });
      return;
    }

    const script = document.createElement('script');
    script.dataset.ybfKakaoMap = 'true';
    script.async = true;
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(kakaoKey.value)}&autoload=false`;
    script.addEventListener('load', () => (window as any).kakao.maps.load(resolve), { once: true });
    script.addEventListener('error', () => reject(new Error('Kakao map SDK failed to load')), { once: true });
    document.head.appendChild(script);
  });

  await (window as any).__ybfKakaoMapPromise;
};

const clearKakaoMarkers = () => {
  for (const marker of renderedMarkers) {
    marker.setMap(null);
  }
  renderedMarkers = [];
};

const focusKakaoMarker = (marker: ComplexMapMarker) => {
  if (!renderedMap || !(window as any).kakao?.maps) return;
  const point = new (window as any).kakao.maps.LatLng(marker.lat, marker.lng);
  renderedMap.panTo(point);
};

const renderKakaoMap = async () => {
  if (!hasMarkers.value || !canUseKakao.value) {
    mapState.value = 'fallback';
    return;
  }

  mapState.value = 'loading';
  await nextTick();

  if (!mapContainer.value || !mapCenter.value) {
    mapState.value = 'fallback';
    return;
  }

  try {
    await loadKakaoSdk();
    const kakao = (window as any).kakao;
    const center = new kakao.maps.LatLng(mapCenter.value.lat, mapCenter.value.lng);

    renderedMap = new kakao.maps.Map(mapContainer.value, {
      center,
      level: props.level
    });
    clearKakaoMarkers();

    for (const marker of props.markers) {
      const kakaoMarker = new kakao.maps.Marker({
        map: renderedMap,
        position: new kakao.maps.LatLng(marker.lat, marker.lng),
        title: marker.name
      });
      kakao.maps.event.addListener(kakaoMarker, 'click', () => setSelectedMarker(marker));
      renderedMarkers.push(kakaoMarker);
    }

    if (selectedMarker.value) {
      focusKakaoMarker(selectedMarker.value);
    }
    mapState.value = 'ready';
  } catch {
    mapState.value = 'error';
  }
};

onMounted(() => {
  void renderKakaoMap();
});

onBeforeUnmount(() => {
  clearKakaoMarkers();
});

watch(() => props.selectedTargetId, (targetId) => {
  selectedMarkerId.value = targetId;
  if (selectedMarker.value) {
    focusKakaoMarker(selectedMarker.value);
  }
});

watch(() => props.markers, () => {
  void renderKakaoMap();
}, { deep: true });
</script>

<template>
  <article class="panel content-feed-card surface-data-card complex-map-panel" data-testid="kakao-complex-map">
    <div class="section-band-title">
      <div>
        <p class="label">embedded map</p>
        <h3>단지 위치 레이어</h3>
      </div>
      <span>{{ displayStatusLabel }}</span>
    </div>

    <div class="complex-map-layout">
      <div class="complex-map-shell" :class="{ 'is-fallback': mapState !== 'ready' }">
        <div ref="mapContainer" class="kakao-map-canvas" data-testid="kakao-map-canvas"></div>
        <div v-if="mapState !== 'ready'" class="complex-map-fallback" data-testid="kakao-map-fallback">
          <button
            v-for="marker in markers"
            :key="marker.targetId"
            type="button"
            :class="['complex-map-pin', marker.tone, { active: marker.targetId === selectedMarker?.targetId }]"
            :style="fallbackPointStyle(marker)"
            :aria-label="`${marker.name} 위치`"
            @click="setSelectedMarker(marker)"
          >
            <span>{{ marker.name }}</span>
          </button>
        </div>
      </div>

      <aside v-if="selectedMarker" class="complex-map-inspector" data-testid="complex-map-inspector">
        <span>{{ selectedMarker.region }} · {{ selectedMarker.dataStatus }}</span>
        <strong>{{ selectedMarker.name }}</strong>
        <p>{{ selectedMarker.address }}</p>
        <dl>
          <div>
            <dt>가격 흐름</dt>
            <dd :class="selectedMarker.tone">{{ selectedMarker.change }}</dd>
          </div>
          <div>
            <dt>관찰 가격</dt>
            <dd>{{ selectedMarker.price }}</dd>
          </div>
          <div>
            <dt>반응</dt>
            <dd>{{ selectedMarker.reaction }}</dd>
          </div>
          <div>
            <dt>기준</dt>
            <dd>{{ selectedMarker.provider }} · {{ selectedMarker.asOf }}</dd>
          </div>
        </dl>
        <em>{{ selectedMarker.note }}</em>
      </aside>
    </div>
  </article>
</template>
