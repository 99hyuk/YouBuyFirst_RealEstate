<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import RealEstateTransactionMap, { type TransactionMapMarker } from '../components/RealEstateTransactionMap.vue';
import { geocodeTransactionItems } from '../lib/kakao-geocode';
import {
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

const regionGroups = regionData.groups as { sido: string; items: { code: string; name: string }[] }[];
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
const activeDealFilter = ref<DealFilter>('all');
const activeSort = ref<TransactionSort>('price-desc');
const query = ref('');
const selectedId = ref('');
const isDetailOpen = ref(false);

const regionName = computed(() => regionNameByCode.get(activeRegion.value) ?? '지역');
const mapCenter = computed(() => regionCentroid(activeRegion.value) ?? undefined);

const visibleItems = computed(() =>
  filterTransactions(
    items.value,
    { propertyType: activePropertyType.value, dealType: activeDealFilter.value, query: query.value },
    activeSort.value
  )
);
// 해당 지역/조건의 실거래 정보 유무를 먼저 판단한다.
const hasTransactionData = computed(() => visibleItems.value.length > 0);
const markers = computed<TransactionMapMarker[]>(() => toTransactionMarkers(visibleItems.value));
const selectedItem = computed(
  () => visibleItems.value.find((item) => item.id === selectedId.value) ?? visibleItems.value[0] ?? null
);
const statusLabel = computed(() => {
  if (loadState.value === 'loading') return '실거래 데이터 불러오는 중';
  if (loadState.value === 'live') return `국토교통부 실거래 · ${regionName.value} · ${visibleItems.value.length}곳`;
  if (loadState.value === 'fallback') return 'mock fallback · 실데이터 수집 전';
  return '실거래 데이터 API 오류';
});
const coordSummary = computed(() => {
  const geocoded = visibleItems.value.filter((item) => item.coordSource === 'geocoded').length;
  return { geocoded, total: visibleItems.value.length };
});
const coordStatusLabel = computed(() => {
  const { geocoded, total } = coordSummary.value;
  if (!total) return '';
  return geocoded ? `실좌표 ${geocoded}/${total}` : '구 중심 좌표(실좌표 0)';
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
    <header class="complex-filter-bar">
      <div class="complex-filter-heading">
        <p class="eyebrow">transaction map · 실거래 지도</p>
        <h2 id="complex-browse-title">실거래 지도</h2>
        <p class="complex-browse-sub">국토교통부 실거래를 건물·단지명으로 묶어 지도에 표시합니다 · 지역을 선택해 보세요</p>
      </div>

      <div class="complex-filter-groups">
        <select
          v-model="activeRegion"
          class="complex-region-select"
          aria-label="지역 선택"
          data-testid="complex-region-select"
          @change="onRegionChange"
        >
          <optgroup v-for="group in regionGroups" :key="group.sido" :label="group.sido">
            <option v-for="region in group.items" :key="region.code" :value="region.code">
              {{ group.sido }} {{ region.name }}
            </option>
          </optgroup>
        </select>

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
      </div>

      <span class="status-pill" :class="{ warning: loadState !== 'live' }" data-testid="complex-status">
        {{ statusLabel }}
      </span>
      <span
        v-if="coordStatusLabel"
        class="status-pill"
        :class="{ warning: coordSummary.geocoded === 0 }"
        data-testid="complex-coord-status"
      >
        {{ coordStatusLabel }}
      </span>
    </header>

    <section class="complex-browse-layout">
      <aside class="complex-list-panel" aria-label="실거래 목록">
        <div v-if="loadState === 'loading'" class="complex-empty">실거래 목록을 불러오는 중입니다…</div>
        <div v-else-if="!hasTransactionData" class="complex-empty complex-empty-nodata">
          실거래 정보 없음
        </div>
        <ul v-else class="complex-card-list">
          <li
            v-for="item in visibleItems"
            :key="item.id"
            :class="['complex-card', { active: item.id === selectedItem?.id }]"
            :data-testid="`complex-card-${item.id}`"
            @click="selectComplex(item)"
          >
            <div class="complex-card-head">
              <span class="complex-deal-badge" :class="item.dealType">{{ dealBadge(item.dealType) }}</span>
              <strong class="complex-name">{{ item.name }}</strong>
              <span v-if="ageBadge(item.builtYear)" class="complex-age-badge">{{ ageBadge(item.builtYear) }}</span>
            </div>
            <p class="complex-price">{{ item.priceLabel }}</p>
            <p class="complex-meta">{{ item.gu }} {{ item.region }} · {{ item.areaLabel }}</p>
            <p class="complex-sub">
              거래 {{ item.dealCount }}건 · 기준 {{ item.asOf }}
              <span v-if="item.stale" class="complex-stale">지연 가능</span>
            </p>
          </li>
        </ul>
      </aside>

      <div class="complex-map-stage">
        <RealEstateTransactionMap
          :markers="markers"
          :selected-target-id="isDetailOpen ? selectedId : ''"
          :center="mapCenter"
          :show-inspector="false"
          :marker-source-status="loadState === 'live' ? `molit 실거래 · ${regionName}` : loadState"
          @select="onMarkerSelect"
          @deselect="closeDetail"
        />

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
          <dl class="transaction-detail-list">
            <div><dt>위치</dt><dd>{{ selectedItem.gu }} {{ selectedItem.region }}</dd></div>
            <div><dt>면적</dt><dd>{{ selectedItem.areaLabel }}</dd></div>
            <div><dt>거래</dt><dd>{{ selectedItem.dealCount }}건</dd></div>
            <div><dt>준공</dt><dd>{{ selectedItem.builtYear ? `${selectedItem.builtYear}년` : '확인 필요' }}</dd></div>
            <div><dt>기준일</dt><dd>{{ selectedItem.asOf }}</dd></div>
          </dl>
          <p class="transaction-detail-note">국토교통부 실거래 · {{ selectedItem.stale ? '지연 가능' : selectedItem.dataStatus }}</p>
        </aside>
      </div>
    </section>
  </section>
</template>
