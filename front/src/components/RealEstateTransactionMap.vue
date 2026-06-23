<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { loadKakaoSdk } from '../lib/kakao-sdk';

export type TransactionMapTone = 'up' | 'down' | 'flat';

export type TransactionMapMarker = {
  targetId: string;
  name: string;
  address: string;
  region: string;
  lat: number;
  lng: number;
  tone: TransactionMapTone;
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
  markers: TransactionMapMarker[];
  selectedTargetId?: string;
  center?: MapCenter;
  level?: number;
  markerSourceStatus?: string;
  showInspector?: boolean;
}>(), {
  selectedTargetId: '',
  level: 5,
  markerSourceStatus: '',
  showInspector: true
});

const emit = defineEmits<{
  select: [marker: TransactionMapMarker];
  deselect: [];
}>();

const mapContainer = ref<HTMLElement | null>(null);
const mapState = ref<'loading' | 'ready' | 'fallback' | 'error'>('loading');
const selectedMarkerId = ref(props.selectedTargetId);

let renderedMap: any = null;
let renderedMarkers: any[] = [];
let overlayElements: { targetId: string; el: HTMLElement }[] = [];

const priceTag = (price: string) => {
  const match = price.match(/[\d,]+(?:\.\d+)?\s*억/);
  return match ? match[0].replace(/\s/g, '') : price;
};

const highlightSelectedOverlay = () => {
  for (const { targetId, el } of overlayElements) {
    const isActive = targetId === selectedMarkerId.value;
    el.classList.toggle('active', isActive);
    el.style.zIndex = isActive ? '20' : '1';
  }
};

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

const fallbackPointStyle = (marker: TransactionMapMarker) => {
  const xDenominator = Math.max(lngRange.value.max - lngRange.value.min, 0.0001);
  const yDenominator = Math.max(latRange.value.max - latRange.value.min, 0.0001);
  const left = ((marker.lng - lngRange.value.min) / xDenominator) * 100;
  const top = (1 - ((marker.lat - latRange.value.min) / yDenominator)) * 100;

  return {
    left: `${Math.min(Math.max(left, 8), 92)}%`,
    top: `${Math.min(Math.max(top, 12), 88)}%`
  };
};

const setSelectedMarker = (marker: TransactionMapMarker) => {
  selectedMarkerId.value = marker.targetId;
  emit('select', marker);
  focusKakaoMarker(marker);
};

const clearKakaoMarkers = () => {
  for (const marker of renderedMarkers) {
    marker.setMap(null);
  }
  renderedMarkers = [];
  overlayElements = [];
};

const focusKakaoMarker = (marker: TransactionMapMarker) => {
  if (!renderedMap || !(window as any).kakao?.maps) return;
  const point = new (window as any).kakao.maps.LatLng(marker.lat, marker.lng);
  renderedMap.panTo(point);
};

// Create the Kakao map once and reuse it; only the overlays are redrawn on data
// changes so dragging the map and background geocoding don't rebuild everything.
const ensureMap = async (): Promise<boolean> => {
  if (renderedMap) return true;
  await loadKakaoSdk(kakaoKey.value);
  const kakao = (window as any).kakao;
  if (!mapContainer.value || !mapCenter.value) return false;
  renderedMap = new kakao.maps.Map(mapContainer.value, {
    center: new kakao.maps.LatLng(mapCenter.value.lat, mapCenter.value.lng),
    level: props.level
  });
  // 지도 빈 영역 클릭 시 상세 패널을 닫도록 알린다.
  kakao.maps.event.addListener(renderedMap, 'click', () => emit('deselect'));
  return true;
};

const drawOverlays = () => {
  const kakao = (window as any).kakao;
  clearKakaoMarkers();
  for (const marker of props.markers) {
    const content = document.createElement('div');
    content.className = `complex-price-overlay ${marker.tone}`;
    content.title = marker.name;
    content.innerHTML = `<span class="price-overlay-amount">${priceTag(marker.price)}</span>`;
    content.addEventListener('click', () => setSelectedMarker(marker));

    const overlay = new kakao.maps.CustomOverlay({
      map: renderedMap,
      position: new kakao.maps.LatLng(marker.lat, marker.lng),
      content,
      yAnchor: 1.25,
      clickable: true
    });
    renderedMarkers.push(overlay);
    overlayElements.push({ targetId: marker.targetId, el: content });
  }
  highlightSelectedOverlay();
};

const renderKakaoMap = async () => {
  if (!hasMarkers.value || !canUseKakao.value) {
    mapState.value = 'fallback';
    return;
  }

  if (!renderedMap) mapState.value = 'loading';
  await nextTick();

  if (!mapContainer.value || !mapCenter.value) {
    mapState.value = 'fallback';
    return;
  }

  try {
    if (!(await ensureMap())) {
      mapState.value = 'fallback';
      return;
    }
    drawOverlays();
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
  highlightSelectedOverlay();
  if (selectedMarker.value) {
    focusKakaoMarker(selectedMarker.value);
  }
});

// Recenter on region change without recreating the map.
watch(() => props.center, (center) => {
  if (renderedMap && center && (window as any).kakao?.maps) {
    renderedMap.setCenter(new (window as any).kakao.maps.LatLng(center.lat, center.lng));
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
            :title="marker.name"
            :aria-label="`${marker.name} ${marker.price}`"
            @click="setSelectedMarker(marker)"
          >
            <span>{{ priceTag(marker.price) }}</span>
          </button>
        </div>
      </div>

      <aside v-if="showInspector && selectedMarker" class="complex-map-inspector" data-testid="complex-map-inspector">
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
