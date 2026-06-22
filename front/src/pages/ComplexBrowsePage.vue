<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import KakaoComplexMap, { type ComplexMapMarker } from '../components/KakaoComplexMap.vue';
import {
  dealTypeLabel,
  fetchComplexBrowse,
  filterComplexes,
  toComplexMarkers,
  type ComplexBrowseItem,
  type ComplexBrowseSort,
  type DealType
} from '../lib/realestate-complex-browse';

type DealFilter = DealType | 'all';

// 네이버 부동산 a=APT:PRE:ABYG:JGC 매물유형 칩. 현재 데이터가 APT만 있어 아파트만 활성.
const propertyTypeChips = [
  { id: 'APT', label: '아파트', active: true },
  { id: 'OPST', label: '오피스텔', active: false },
  { id: 'ABYG', label: '재건축', active: false },
  { id: 'PRE', label: '분양권', active: false },
  { id: 'JGC', label: '재개발', active: false }
];
const dealFilters: { id: DealFilter; label: string }[] = [
  { id: 'all', label: '전체' },
  { id: 'trade', label: '매매' },
  { id: 'rent', label: '전·월세' }
];
const sortOptions: { id: ComplexBrowseSort; label: string }[] = [
  { id: 'price-desc', label: '가격 높은순' },
  { id: 'price-asc', label: '가격 낮은순' },
  { id: 'count-desc', label: '거래 많은순' }
];

const items = ref<ComplexBrowseItem[]>([]);
const loadState = ref<'loading' | 'live' | 'fallback' | 'error'>('loading');
const activeDealFilter = ref<DealFilter>('all');
const activeSort = ref<ComplexBrowseSort>('price-desc');
const query = ref('');
const selectedId = ref('');

const visibleItems = computed(() =>
  filterComplexes(items.value, { dealType: activeDealFilter.value, query: query.value }, activeSort.value)
);
const markers = computed<ComplexMapMarker[]>(() => toComplexMarkers(visibleItems.value));
const selectedItem = computed(
  () => visibleItems.value.find((item) => item.id === selectedId.value) ?? visibleItems.value[0] ?? null
);
const statusLabel = computed(() => {
  if (loadState.value === 'loading') return '단지 데이터 불러오는 중';
  if (loadState.value === 'live') return `국토교통부 실거래 · ${visibleItems.value.length}개 단지`;
  if (loadState.value === 'fallback') return 'mock fallback · 실데이터 수집 전';
  return '단지 데이터 API 오류';
});

const refreshComplexes = async () => {
  loadState.value = 'loading';
  try {
    const result = await fetchComplexBrowse();
    items.value = result.items;
    selectedId.value = result.items[0]?.id ?? '';
    loadState.value = result.source === 'live' ? 'live' : 'fallback';
  } catch {
    items.value = [];
    loadState.value = 'error';
  }
};

const selectComplex = (item: ComplexBrowseItem) => {
  selectedId.value = item.id;
};
const onMarkerSelect = (marker: ComplexMapMarker) => {
  selectedId.value = marker.targetId;
};
const dealBadge = (dealType: DealType) => dealTypeLabel(dealType);

onMounted(() => {
  void refreshComplexes();
});
</script>

<template>
  <section class="complex-browse-page" aria-labelledby="complex-browse-title">
    <header class="complex-filter-bar">
      <div class="complex-filter-heading">
        <p class="eyebrow">complex browser · 단지 지도</p>
        <h2 id="complex-browse-title">단지로 보는 실거래 지도</h2>
      </div>

      <div class="complex-filter-groups">
        <div class="filter-chip-row" aria-label="매물 유형">
          <button
            v-for="chip in propertyTypeChips"
            :key="chip.id"
            type="button"
            class="filter-chip"
            :class="{ active: chip.active }"
            :disabled="!chip.active"
            :title="chip.active ? '' : '현재 데이터는 아파트만 제공됩니다'"
          >
            {{ chip.label }}
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
          <input v-model="query" type="search" placeholder="단지명·지역 검색" aria-label="단지명 또는 지역 검색" />
        </label>

        <select v-model="activeSort" class="complex-sort" aria-label="정렬 기준">
          <option v-for="option in sortOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
        </select>
      </div>

      <span class="status-pill" :class="{ warning: loadState !== 'live' }" data-testid="complex-status">
        {{ statusLabel }}
      </span>
    </header>

    <section class="complex-browse-layout">
      <aside class="complex-list-panel" aria-label="단지 목록">
        <div v-if="loadState === 'loading'" class="complex-empty">단지 목록을 불러오는 중입니다…</div>
        <div v-else-if="!visibleItems.length" class="complex-empty">
          조건에 맞는 단지가 없습니다. 필터를 조정해 보세요.
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
            </div>
            <p class="complex-price" :class="item.tone">{{ item.priceLabel }}</p>
            <p class="complex-meta">{{ item.gu }} {{ item.region }} · {{ item.areaLabel }}</p>
            <p class="complex-sub">
              거래 {{ item.dealCount }}건 · 기준 {{ item.asOf }}
              <span v-if="item.stale" class="complex-stale">지연 가능</span>
            </p>
          </li>
        </ul>
      </aside>

      <div class="complex-map-stage">
        <KakaoComplexMap
          :markers="markers"
          :selected-target-id="selectedItem?.id ?? ''"
          :marker-source-status="loadState === 'live' ? 'molit 실거래' : loadState"
          @select="onMarkerSelect"
        />
      </div>
    </section>
  </section>
</template>
