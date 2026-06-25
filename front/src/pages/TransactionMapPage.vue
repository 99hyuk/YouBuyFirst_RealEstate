<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import RealEstateTransactionMap, { type TransactionMapMarker } from '../components/RealEstateTransactionMap.vue';
import { geocodeTransactionItems } from '../lib/kakao-geocode';
import { formatDistance } from '../lib/geo-distance';
import { fetchNearbyFacilities, type NearbyFacilities } from '../lib/kakao-nearby-places';
import {
  computeTransactionChange,
  computeTransactionPriceTrend,
  dealTypeLabel,
  fetchTransactions,
  filterTransactions,
  regionCentroid,
  toTransactionMarkers,
  type TransactionItem,
  type TransactionSort,
  type DealType,
  type PropertyType
} from '../lib/realestate-transaction-browse';
import regionData from '../fixtures/transaction-regions.json';

type DealFilter = DealType | 'all';
type TransactionRegionGroup = { sido: string; items: { code: string; name: string }[] };
type SidoOption = TransactionRegionGroup & { code: string };

const regionGroups = regionData.groups as TransactionRegionGroup[];
const sidoOptions: SidoOption[] = regionGroups
  .map((group) => ({ ...group, code: group.items[0]?.code.slice(0, 2) ?? '' }))
  .filter((group) => group.code);
const regionGroupBySido = new Map(sidoOptions.map((group) => [group.code, group]));
const sidoByRegionCode = new Map(
  sidoOptions.flatMap((group) => group.items.map((item) => [item.code, group.code] as const))
);
const regionNameByCode = new Map(regionGroups.flatMap((group) => group.items.map((item) => [item.code, item.name])));
const regionCodes = [...regionNameByCode.keys()];

// 다른 페이지(지역 분석)에서 ?region=<시군구코드> 또는 시도 2자리 prefix로 진입 가능.
function resolveInitialRegion(requested: unknown): string {
  const code = (Array.isArray(requested) ? requested[0] : requested) ?? '';
  const value = String(code).trim();
  if (regionNameByCode.has(value)) return value;
  if (/^\d{2}$/.test(value)) {
    const match = regionCodes.find((regionCode) => regionCode.startsWith(value));
    if (match) return match;
  }
  return '11680';
}

const route = useRoute();

// 매물유형 카테고리. value가 있으면 실데이터 연결(활성).
// 단독·다가구는 단지명이 없어 지번 주소로 라벨링한다. 재건축/재개발은 수집 데이터가 없어 준비중.
const propertyTypeChips: { id: string; label: string; value?: PropertyType; note?: string }[] = [
  { id: 'APT', label: '아파트', value: 'apt' },
  { id: 'OPST', label: '오피스텔', value: 'offi' },
  { id: 'RH', label: '연립·다세대', value: 'rh' },
  { id: 'SILV', label: '분양권', value: 'silv' },
  { id: 'SH', label: '단독·다가구', value: 'sh' },
  { id: 'ABYG', label: '재건축', note: '준비중' },
  { id: 'JGC', label: '재개발', note: '준비중' }
];
const dealFilters: { id: DealFilter; label: string }[] = [
  { id: 'all', label: '전체' },
  { id: 'trade', label: '매매' },
  { id: 'rent', label: '전·월세' }
];
const sortOptions: { id: TransactionSort; label: string }[] = [
  { id: 'price-desc', label: '가격 높은순' },
  { id: 'price-asc', label: '가격 낮은순' },
  { id: 'count-desc', label: '거래 많은순' }
];

const items = ref<TransactionItem[]>([]);
let loadToken = 0;
const loadState = ref<'loading' | 'live' | 'fallback' | 'error'>('loading');
const activePropertyType = ref<PropertyType>('apt');
const activeRegion = ref<string>(resolveInitialRegion(route.query.region));
const activeSido = ref<string>(sidoByRegionCode.get(activeRegion.value) ?? activeRegion.value.slice(0, 2));
const activeDealFilter = ref<DealFilter>('all');
const activeSort = ref<TransactionSort>('price-desc');
const query = ref('');
const selectedId = ref('');
const isDetailOpen = ref(false);

const activeRegionOptions = computed(() => regionGroupBySido.get(activeSido.value)?.items ?? []);
const regionName = computed(() => regionNameByCode.get(activeRegion.value) ?? '지역');
const mapCenter = computed(() => regionCentroid(activeRegion.value) ?? undefined);

const visibleItems = computed(() =>
  filterTransactions(
    items.value,
    { propertyType: activePropertyType.value, dealType: activeDealFilter.value, query: query.value },
    activeSort.value
  )
);
// 실좌표(카카오 지오코딩)가 적용된 건물만 지도/목록에 노출하고, 미적용 건물은 별도 목록으로 분리한다.
const geocodedItems = computed(() => visibleItems.value.filter((item) => item.coordSource === 'geocoded'));
const pendingItems = computed(() => visibleItems.value.filter((item) => item.coordSource !== 'geocoded'));
// 실좌표 미적용 건물 포함 여부(필터 토글). 켜면 기존 목록에 미적용 건물도 합쳐 정렬된 채로 보여준다.
const showPending = ref(false);
const listItems = computed(() => (showPending.value ? visibleItems.value : geocodedItems.value));
const listState = computed<'loading' | 'empty' | 'ready'>(() => {
  if (loadState.value === 'loading') return 'loading';
  if (!visibleItems.value.length) return 'empty';
  return 'ready';
});
// 지도 마커는 실좌표가 있는 건물만(좌표 없는 건 위치가 부정확해 제외).
// 마커 색은 선택한 비교 기간(YoY/6개월/MoM)을 따른다 → 기간 전환 시 지도 색이 함께 바뀜.
const markers = computed<TransactionMapMarker[]>(() => toTransactionMarkers(geocodedItems.value, activeTrendPeriod.value));
const selectedItem = computed(
  () => visibleItems.value.find((item) => item.id === selectedId.value) ?? null
);
// 선택 매물 주변(1km 이내) 지하철역/버스정류장/편의점·마트 검색. 선택이 바뀔 때마다 재검색.
const nearbyState = ref<'idle' | 'loading' | 'ready' | 'unavailable'>('idle');
const nearbyFacilities = ref<NearbyFacilities | null>(null);
watch(selectedId, async (id) => {
  const target = selectedItem.value;
  if (!id || !target) {
    nearbyState.value = 'idle';
    nearbyFacilities.value = null;
    return;
  }
  nearbyState.value = 'loading';
  const result = await fetchNearbyFacilities({ lat: target.lat, lng: target.lng });
  if (selectedId.value !== id) return; // 검색 도중 다른 매물이 선택된 경우 결과 무시.
  if (!result) {
    nearbyState.value = 'unavailable';
    nearbyFacilities.value = null;
    return;
  }
  nearbyFacilities.value = result;
  nearbyState.value = 'ready';
});
const refreshComplexes = async () => {
  const token = ++loadToken;
  loadState.value = 'loading';
  try {
    const result = await fetchTransactions(activePropertyType.value, activeRegion.value);
    if (token !== loadToken) return;
    items.value = result.items;
    // 초기에는 상세 패널을 닫아두고, 마커/카드 클릭 시에만 연다.
    selectedId.value = '';
    isDetailOpen.value = false;
    loadState.value = result.source === 'live' ? 'live' : 'fallback';
    // Resolve real complex coordinates in the background; markers update once done.
    void applyGeocoding(result.items, token);
  } catch {
    if (token !== loadToken) return;
    items.value = [];
    loadState.value = 'error';
  }
};

const applyGeocoding = async (base: TransactionItem[], token: number) => {
  const geocoded = await geocodeTransactionItems(base);
  // Only apply if a newer load hasn't superseded this one.
  if (token === loadToken) {
    items.value = geocoded;
  }
};

const selectPropertyType = (value: PropertyType) => {
  if (activePropertyType.value === value) return;
  activePropertyType.value = value;
  void refreshComplexes();
};

const onRegionChange = () => {
  activeSido.value = sidoByRegionCode.get(activeRegion.value) ?? activeSido.value;
  void refreshComplexes();
};

const onSidoChange = () => {
  const firstRegion = activeRegionOptions.value[0]?.code;
  if (firstRegion) {
    activeRegion.value = firstRegion;
  }
  void refreshComplexes();
};

const selectComplex = (item: TransactionItem) => {
  selectedId.value = item.id;
  isDetailOpen.value = true;
};
const onMarkerSelect = (marker: TransactionMapMarker) => {
  selectedId.value = marker.targetId;
  isDetailOpen.value = true;
};
const closeDetail = () => {
  isDetailOpen.value = false;
};
const dealBadge = (dealType: DealType) => dealTypeLabel(dealType);

type TrendPeriod = 'yoy' | '6m' | 'mom';
const trendPeriods: { id: TrendPeriod; label: string; caption: string }[] = [
  { id: 'yoy', label: 'YoY', caption: '전년 동월 대비' },
  { id: '6m', label: '6개월', caption: '6개월 전 대비' },
  { id: 'mom', label: 'MoM', caption: '전월 대비' }
];
const activeTrendPeriod = ref<TrendPeriod>('yoy');
const activeTrendCaption = computed(
  () => trendPeriods.find((period) => period.id === activeTrendPeriod.value)?.caption ?? ''
);
// 선택 단지의 활성 기간(YoY/6개월/MoM) ▲/▼ 변동률 + 이전→현재 가격. 비교 데이터 없으면 null.
const selectedPriceTrend = computed(() =>
  computeTransactionPriceTrend(selectedItem.value, activeTrendPeriod.value)
);

// 리스트 가격 색: 선택한 비교 기간(YoY/6개월/MoM) 변동이 있으면 상승=빨강/하락=파랑, 없으면 기본색.
const priceTone = (item: TransactionItem): '' | 'up' | 'down' => {
  const change = computeTransactionChange(item, activeTrendPeriod.value);
  if (change === null || change === 0) return '';
  return change > 0 ? 'up' : 'down';
};

// 준공연도 기준 신축/구축 라벨(색이 아닌 명시적 텍스트로 표시).
const ageBadge = (builtYear: number | null) => {
  if (builtYear === null) return '';
  if (builtYear >= 2015) return '신축';
  if (builtYear <= 2005) return '구축';
  return '';
};

onMounted(() => {
  void refreshComplexes();
});
</script>

<template>
  <section class="complex-browse-page" aria-labelledby="complex-browse-title">
    <header class="complex-filter-bar floating" aria-label="실거래 지도 필터">
      <h2 id="complex-browse-title" class="overlay-title">실거래 지도</h2>

      <div class="complex-filter-groups">
        <div class="complex-region-picker" aria-label="지역 선택">
          <select
            v-model="activeSido"
            class="complex-sido-select"
            aria-label="시도 선택"
            data-testid="complex-sido-select"
            @change="onSidoChange"
          >
            <option v-for="group in sidoOptions" :key="group.code" :value="group.code">
              {{ group.sido }}
            </option>
          </select>

          <select
            v-model="activeRegion"
            class="complex-region-select"
            aria-label="시군구 선택"
            data-testid="complex-region-select"
            @change="onRegionChange"
          >
            <option v-for="region in activeRegionOptions" :key="region.code" :value="region.code">
              {{ region.name }}
            </option>
          </select>
        </div>

        <div class="filter-chip-row" aria-label="매물 유형">
          <button
            v-for="chip in propertyTypeChips"
            :key="chip.id"
            type="button"
            class="filter-chip"
            :class="{ active: chip.value && activePropertyType === chip.value, pending: !chip.value }"
            :disabled="!chip.value"
            :title="chip.note ?? ''"
            @click="chip.value && selectPropertyType(chip.value)"
          >
            {{ chip.label }}<small v-if="chip.note"> {{ chip.note }}</small>
          </button>
        </div>

        <div class="filter-chip-row" aria-label="거래 방식">
          <button
            v-for="deal in dealFilters"
            :key="deal.id"
            type="button"
            class="filter-chip deal"
            :class="{ active: activeDealFilter === deal.id }"
            @click="activeDealFilter = deal.id"
          >
            {{ deal.label }}
          </button>
        </div>

        <label class="complex-search">
          <input v-model="query" type="search" placeholder="건물·단지명·지역 검색" aria-label="건물·단지명 또는 지역 검색" />
        </label>

        <select v-model="activeSort" class="complex-sort" aria-label="정렬 기준">
          <option v-for="option in sortOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
        </select>

        <div class="filter-chip-row" role="radiogroup" aria-label="가격 비교 기간">
          <button
            v-for="period in trendPeriods"
            :key="period.id"
            type="button"
            class="filter-chip"
            role="radio"
            :aria-checked="activeTrendPeriod === period.id"
            :class="{ active: activeTrendPeriod === period.id }"
            :title="period.caption"
            @click="activeTrendPeriod = period.id"
          >
            {{ period.label }}
          </button>
        </div>
      </div>
    </header>

    <div class="complex-map-stage">
      <RealEstateTransactionMap
        class="complex-map-canvas"
        :markers="markers"
        :selected-target-id="isDetailOpen ? selectedId : ''"
        :center="mapCenter"
        :show-inspector="false"
        :marker-source-status="loadState === 'live' ? `molit 실거래 · ${regionName}` : loadState"
        @select="onMarkerSelect"
        @deselect="closeDetail"
      />

      <aside class="complex-list-panel floating" aria-label="실거래 목록">
      <div v-if="listState === 'loading'" class="complex-empty">실거래 목록을 불러오는 중입니다…</div>
      <div v-else-if="listState === 'empty'" class="complex-empty complex-empty-nodata">
        실거래 정보 없음
      </div>
      <template v-else>
        <ul v-if="listItems.length" class="complex-card-list">
          <li
            v-for="item in listItems"
            :key="item.id"
            :class="['complex-card', { active: item.id === selectedItem?.id }]"
            :data-testid="`complex-card-${item.id}`"
            @click="selectComplex(item)"
          >
            <div class="complex-card-head">
              <span class="complex-deal-badge" :class="item.dealType">{{ dealBadge(item.dealType) }}</span>
              <strong class="complex-name">{{ item.name }}</strong>
              <span v-if="ageBadge(item.builtYear)" class="complex-age-badge">{{ ageBadge(item.builtYear) }}</span>
              <span v-if="item.coordSource !== 'geocoded'" class="complex-coord-badge">근사좌표</span>
            </div>
            <p class="complex-price" :class="priceTone(item)">{{ item.priceLabel }}</p>
            <p class="complex-meta">{{ item.gu }} {{ item.region }} · {{ item.areaLabel }}</p>
            <p class="complex-sub">
              거래 {{ item.dealCount }}건 · 기준 {{ item.asOf }}
              <span v-if="item.stale" class="complex-stale">지연 가능</span>
            </p>
          </li>
        </ul>
        <div v-else class="complex-empty">실좌표 확인 중…</div>
        <button
          v-if="pendingItems.length"
          type="button"
          class="pending-toggle"
          :class="{ active: showPending }"
          data-testid="pending-toggle"
          @click="showPending = !showPending"
        >
          {{ showPending ? '실좌표 미적용 건물 숨기기' : `실좌표 미적용 건물 ${pendingItems.length}건 포함` }}
        </button>
      </template>
    </aside>

    <aside
      v-if="selectedItem"
      class="transaction-detail"
      :class="{ open: isDetailOpen }"
      data-testid="transaction-detail"
      aria-label="실거래 상세 정보"
    >
      <button class="transaction-detail-close" type="button" aria-label="상세 정보 닫기" @click="closeDetail">×</button>
      <span class="transaction-detail-badge" :class="selectedItem.dealType">{{ dealBadge(selectedItem.dealType) }}</span>
      <strong class="transaction-detail-name">{{ selectedItem.name }}</strong>
      <p class="transaction-detail-price">{{ selectedItem.priceLabel }}</p>

      <div class="transaction-trend">
        <div class="transaction-trend-tabs" role="radiogroup" aria-label="상세 비교 기간">
          <button
            v-for="period in trendPeriods"
            :key="period.id"
            type="button"
            class="transaction-trend-tab"
            role="radio"
            :aria-checked="activeTrendPeriod === period.id"
            :class="{ active: activeTrendPeriod === period.id }"
            :title="period.caption"
            @click="activeTrendPeriod = period.id"
          >
            {{ period.label }}
          </button>
        </div>
        <template v-if="selectedPriceTrend">
          <p
            class="transaction-trend-mom-rate"
            :class="selectedPriceTrend.changePercent > 0 ? 'up' : selectedPriceTrend.changePercent < 0 ? 'down' : 'flat'"
            data-testid="transaction-trend-rate"
          >
            {{ activeTrendCaption }}
            {{ selectedPriceTrend.changePercent > 0 ? '▲' : selectedPriceTrend.changePercent < 0 ? '▼' : '–' }}
            {{ Math.abs(selectedPriceTrend.changePercent) }}%
          </p>
          <p class="transaction-trend-mom-prices" data-testid="transaction-trend-prices">
            {{ selectedPriceTrend.previousLabel }} → {{ selectedPriceTrend.currentLabel }}
          </p>
        </template>
        <p v-else class="transaction-trend-empty" data-testid="transaction-trend-empty">
          {{ activeTrendCaption }} · 비교데이터 없음 (해당 매물유형/기간은 아직 비교월 데이터가 수집되지 않았습니다)
        </p>
      </div>
      <dl class="transaction-detail-list">
        <div><dt>위치</dt><dd>{{ selectedItem.gu }} {{ selectedItem.region }}</dd></div>
        <div><dt>면적</dt><dd>{{ selectedItem.areaLabel }}</dd></div>
        <div><dt>거래</dt><dd>{{ selectedItem.dealCount }}건</dd></div>
        <div><dt>준공</dt><dd>{{ selectedItem.builtYear ? `${selectedItem.builtYear}년` : '확인 필요' }}</dd></div>
        <div><dt>기준일</dt><dd>{{ selectedItem.asOf }}</dd></div>
      </dl>

      <div class="transaction-nearby" data-testid="transaction-nearby">
        <p class="transaction-nearby-title">주변 시설</p>
        <ul v-if="nearbyState === 'ready' && nearbyFacilities" class="transaction-nearby-list">
          <li v-if="nearbyFacilities.subway" class="transaction-nearby-item">
            <span class="transaction-nearby-icon" aria-hidden="true">🚇</span>
            <span class="transaction-nearby-name">{{ nearbyFacilities.subway.name }}</span>
            <span class="transaction-nearby-distance">{{ formatDistance(nearbyFacilities.subway.distanceMeters) }}</span>
          </li>
          <li v-if="nearbyFacilities.bus" class="transaction-nearby-item">
            <span class="transaction-nearby-icon" aria-hidden="true">🚌</span>
            <span class="transaction-nearby-name">{{ nearbyFacilities.bus.name }}</span>
            <span class="transaction-nearby-distance">{{ formatDistance(nearbyFacilities.bus.distanceMeters) }}</span>
          </li>
          <li v-if="nearbyFacilities.store" class="transaction-nearby-item">
            <span class="transaction-nearby-icon" aria-hidden="true">🏪</span>
            <span class="transaction-nearby-name">{{ nearbyFacilities.store.name }}</span>
            <span class="transaction-nearby-distance">{{ formatDistance(nearbyFacilities.store.distanceMeters) }}</span>
          </li>
          <li
            v-if="!nearbyFacilities.subway && !nearbyFacilities.bus && !nearbyFacilities.store"
            class="transaction-nearby-empty"
          >
            주변 1km 이내 시설 정보 없음
          </li>
        </ul>
        <p v-else-if="nearbyState === 'loading'" class="transaction-nearby-empty">주변 시설 검색 중…</p>
        <p v-else class="transaction-nearby-empty">주변 시설 정보 없음</p>
      </div>

      <p class="transaction-detail-note">국토교통부 실거래 · {{ selectedItem.stale ? '지연 가능' : selectedItem.dataStatus }}</p>
    </aside>
    </div>
  </section>
</template>
