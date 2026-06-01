<script setup lang="ts">
import { geoCentroid, geoMercator, geoPath } from 'd3-geo';
import type { Feature, FeatureCollection, Geometry, Position } from 'geojson';
import { feature as topojsonFeature } from 'topojson-client';
import type { GeometryCollection, Topology } from 'topojson-specification';
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import mapFixture from '../fixtures/realestate-map-targets.json';
import municipalitiesTopo from '../fixtures/skorea-municipalities-2018-topo-simple.json';
import koreaProvincesTopo from '../fixtures/skorea-provinces-2018-topo-simple.json';

type PeriodKey = 'week' | 'month' | 'halfYear';
type ReportKey =
  | 'priceFlow'
  | 'tradeStrength'
  | 'jeonsePressure'
  | 'supplySignal'
  | 'policyEvent'
  | 'communityReaction';
type MapTarget = (typeof mapFixture.targets)[number];
type ProvinceProperties = {
  base_year: string;
  code: string;
  name: string;
  name_eng: string;
};
type MunicipalityProperties = ProvinceProperties;
type ProvinceFeature = Feature<Geometry, ProvinceProperties>;
type MunicipalityFeature = Feature<Geometry, MunicipalityProperties>;
type KoreaTopology = Topology<{
  skorea_provinces_2018_geo: GeometryCollection<ProvinceProperties>;
}>;
type MunicipalityTopology = Topology<{
  skorea_municipalities_2018_geo: GeometryCollection<MunicipalityProperties>;
}>;
type MapFeature = {
  code: string;
  label: { x: number; y: number };
  path: string;
  pathTransform?: string;
  provinceName: string;
  target: MapTarget;
};
type SubregionFeature = {
  code: string;
  label: { x: number; y: number };
  name: string;
  nameEng: string;
  parent: MapTarget;
  path: string;
};
type IssueCard = {
  detail: string;
  label: string;
  risk: string;
};

const route = useRoute();
const router = useRouter();

const periodOptions: { id: PeriodKey; label: string }[] = [
  { id: 'week', label: '1주' },
  { id: 'month', label: '1개월' },
  { id: 'halfYear', label: '6개월' }
];
const periodLabelById: Record<PeriodKey, string> = {
  week: '최근 1주',
  month: '최근 1개월',
  halfYear: '최근 6개월'
};
const metricLabels: { key: ReportKey; label: string }[] = [
  { label: '가격 흐름', key: 'priceFlow' },
  { label: '거래 강도', key: 'tradeStrength' },
  { label: '전세 압력', key: 'jeonsePressure' },
  { label: '공급/청약', key: 'supplySignal' },
  { label: '정책/교통', key: 'policyEvent' },
  { label: '커뮤니티 언급', key: 'communityReaction' }
];

const activePeriod = ref<PeriodKey>('month');
const selectedSubregionCode = ref<string | null>(null);
const reportOpening = ref(false);
const reportSettled = ref(true);
let reportOpeningTimer: number | undefined;
let reportSettledTimer: number | undefined;

const targets = mapFixture.targets;
const nationalMapSize = { width: 430, height: 630 };
const detailMapSize = { width: 560, height: 560 };
const currentMapSize = computed(() => (selectedRegion.value ? detailMapSize : nationalMapSize));

const koreaTopology = koreaProvincesTopo as KoreaTopology;
const municipalityTopology = municipalitiesTopo as MunicipalityTopology;
const provinceFeatureCollection = topojsonFeature(
  koreaTopology,
  koreaTopology.objects.skorea_provinces_2018_geo
) as FeatureCollection<Geometry, ProvinceProperties>;
const municipalityFeatureCollection = topojsonFeature(
  municipalityTopology,
  municipalityTopology.objects.skorea_municipalities_2018_geo
) as FeatureCollection<Geometry, MunicipalityProperties>;

const polygonArea = (ring: Position[]) => {
  if (ring.length < 3) return 0;

  return Math.abs(
    ring.reduce((sum, point, index) => {
      const previous = ring[index === 0 ? ring.length - 1 : index - 1];

      return sum + (previous[0] * point[1] - point[0] * previous[1]);
    }, 0) / 2
  );
};

const trimSmallMultipolygons = <P,>(feature: Feature<Geometry, P>, minRatio = 0.05): Feature<Geometry, P> => {
  if (feature.geometry.type !== 'MultiPolygon') return feature;

  const polygons = feature.geometry.coordinates.map((polygon) => ({
    area: polygonArea(polygon[0] ?? []),
    polygon
  }));
  const largestArea = Math.max(...polygons.map((polygon) => polygon.area));
  const visiblePolygons = polygons
    .filter((polygon) => polygon.area === largestArea || polygon.area >= largestArea * minRatio)
    .map((polygon) => polygon.polygon);

  return {
    ...feature,
    geometry: {
      ...feature.geometry,
      coordinates: visiblePolygons
    }
  };
};

const provinceDisplayCollection: FeatureCollection<Geometry, ProvinceProperties> = {
  ...provinceFeatureCollection,
  features: provinceFeatureCollection.features.map((feature) => trimSmallMultipolygons(feature as ProvinceFeature, 0.04))
};
const countryOutlineFeatureCollection: FeatureCollection<Geometry, ProvinceProperties> = {
  ...provinceDisplayCollection,
  features: provinceDisplayCollection.features.filter((feature) => feature.properties.code !== '39')
};
const targetByRegionCode = new Map(targets.map((target) => [target.regionCode, target]));
const targetById = new Map(targets.map((target) => [target.id, target]));
const nationalProjection = geoMercator().fitSize([nationalMapSize.width, nationalMapSize.height], provinceDisplayCollection);
const nationalPathGenerator = geoPath(nationalProjection);
const countryPath = nationalPathGenerator(countryOutlineFeatureCollection) ?? '';
const mapFeatures = provinceDisplayCollection.features.reduce<MapFeature[]>((items, feature: ProvinceFeature) => {
  const target = targetByRegionCode.get(feature.properties.code);
  const path = nationalPathGenerator(feature);
  const centroid = nationalProjection(geoCentroid(feature));

  if (!target || !path || !centroid) return items;

  const visualOffsetY = target.id === 'jeju' ? -56 : 0;

  items.push({
    code: feature.properties.code,
    label: { x: centroid[0], y: centroid[1] + visualOffsetY },
    path,
    pathTransform: visualOffsetY ? `translate(0 ${visualOffsetY})` : undefined,
    provinceName: feature.properties.name,
    target
  });

  return items;
}, []);
const samplePins = mapFeatures.filter((feature) => ['seoul', 'gyeonggi', 'busan'].includes(feature.target.id));
const compactRegionIds = new Set(['seoul', 'incheon', 'sejong', 'daejeon', 'daegu', 'gwangju', 'ulsan', 'busan']);
const labelOffsetByRegionId: Record<string, { x: number; y: number }> = {
  busan: { x: 38, y: 20 },
  chungbuk: { x: 26, y: -4 },
  chungnam: { x: -36, y: 18 },
  daegu: { x: 42, y: 26 },
  daejeon: { x: 16, y: 28 },
  gangwon: { x: 26, y: -8 },
  gwangju: { x: -50, y: 2 },
  gyeongbuk: { x: 34, y: -18 },
  gyeonggi: { x: 42, y: -44 },
  gyeongnam: { x: -10, y: 28 },
  incheon: { x: -38, y: -12 },
  jeju: { x: 0, y: -10 },
  jeonbuk: { x: -28, y: -4 },
  jeonnam: { x: -26, y: 34 },
  sejong: { x: -10, y: -32 },
  seoul: { x: 8, y: -4 },
  ulsan: { x: 42, y: -18 }
};

const routeRegionId = computed(() => String(route.params.regionId ?? '').toLowerCase());
const selectedRegion = computed(() => targetById.get(routeRegionId.value) ?? null);
const layoutMode = computed(() => (selectedReport.value ? 'split' : 'centered'));
const pageTitle = computed(() => (selectedRegion.value ? `${selectedRegion.value.name} 상세 흐름 지도` : '전국 지역 흐름 지도'));
const pageDescription = computed(() =>
  selectedRegion.value
    ? `${selectedRegion.value.name} 안의 구·시·군을 실제 행정구역 경계로 나누고, 기간별 상승·하락 흐름과 커뮤니티 반응을 함께 봅니다.`
    : '전국 시도별 가격 흐름과 커뮤니티 반응을 3D 관찰형 지도 위에 겹쳐 보여줍니다. 지역을 누르면 해당 시도의 구·시·군 상세 지도로 이동합니다.'
);

const selectedMunicipalityCollection = computed<FeatureCollection<Geometry, MunicipalityProperties>>(() => {
  if (!selectedRegion.value) {
    return {
      type: 'FeatureCollection',
      features: []
    };
  }

  return {
    type: 'FeatureCollection',
    features: municipalityFeatureCollection.features
      .filter((feature) => feature.properties.code.startsWith(selectedRegion.value!.regionCode))
      .map((feature) => trimSmallMultipolygons(feature as MunicipalityFeature, 0.04) as MunicipalityFeature)
  };
});
const detailProjection = computed(() => {
  const collection = selectedMunicipalityCollection.value;

  return geoMercator().fitSize(
    [detailMapSize.width, detailMapSize.height],
    collection.features.length ? collection : provinceDisplayCollection
  );
});
const detailPathGenerator = computed(() => geoPath(detailProjection.value));
const detailOutlinePath = computed(() => detailPathGenerator.value(selectedMunicipalityCollection.value) ?? '');
const subregionFeatures = computed<SubregionFeature[]>(() => {
  if (!selectedRegion.value) return [];

  return selectedMunicipalityCollection.value.features.reduce<SubregionFeature[]>((items, feature) => {
    const path = detailPathGenerator.value(feature);
    const centroid = detailProjection.value(geoCentroid(feature));

    if (!path || !centroid) return items;

    items.push({
      code: feature.properties.code,
      label: { x: centroid[0], y: centroid[1] },
      name: feature.properties.name,
      nameEng: feature.properties.name_eng,
      parent: selectedRegion.value!,
      path
    });

    return items;
  }, []);
});
const selectedSubregion = computed(
  () => subregionFeatures.value.find((feature) => feature.code === selectedSubregionCode.value) ?? null
);
const strongestRegion = computed(() =>
  [...targets].sort(
    (left, right) => Math.abs(right.periodChanges[activePeriod.value]) - Math.abs(left.periodChanges[activePeriod.value])
  )[0]
);
const strongestSubregion = computed(() =>
  [...subregionFeatures.value].sort(
    (left, right) =>
      Math.abs(subregionPeriodChange(right, activePeriod.value)) - Math.abs(subregionPeriodChange(left, activePeriod.value))
  )[0]
);

const periodChange = (target: MapTarget) => target.periodChanges[activePeriod.value];
const formatChange = (value: number) => `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
const changeTone = (value: number) => {
  if (value > 0.04) return 'up';
  if (value < -0.04) return 'down';
  return 'flat';
};
const heatColor = (value: number) => {
  const intensity = Math.min(1, Math.max(0.12, Math.abs(value) / 0.65));
  if (value > 0.04) return `rgba(255, 54, 88, ${0.3 + intensity * 0.66})`;
  if (value < -0.04) return `rgba(42, 125, 255, ${0.28 + intensity * 0.62})`;
  return 'rgba(126, 143, 166, 0.42)';
};
const numberSeed = (value: string) =>
  value.split('').reduce((sum, char, index) => sum + Number.parseInt(char, 10) * (index + 1), 0);
const subregionPeriodChange = (feature: SubregionFeature, period: PeriodKey = activePeriod.value) => {
  const spreadByPeriod: Record<PeriodKey, number> = {
    week: 0.09,
    month: 0.28,
    halfYear: 0.72
  };
  const seedOffset = ((numberSeed(feature.code) % 13) - 6) / 6;

  return Number((feature.parent.periodChanges[period] + seedOffset * spreadByPeriod[period]).toFixed(2));
};
const subregionSampleCount = (feature: SubregionFeature) => {
  const divisor = Math.max(1, subregionFeatures.value.length);
  const base = feature.parent.sampleCount / divisor;
  const multiplier = 0.82 + (numberSeed(feature.code) % 7) * 0.07;

  return Math.max(9, Math.round(base * multiplier));
};
const subregionConfidence = (feature: SubregionFeature) =>
  Math.max(38, Math.min(92, feature.parent.confidence - 8 + (numberSeed(feature.code) % 19)));
const labelButtonStyle = (feature: MapFeature) => {
  const offset = labelOffsetByRegionId[feature.target.id] ?? { x: 0, y: 0 };

  return {
    left: `${((feature.label.x + offset.x) / nationalMapSize.width) * 100}%`,
    top: `${((feature.label.y + offset.y - 4) / nationalMapSize.height) * 100}%`,
    zIndex: compactRegionIds.has(feature.target.id) ? 4 : 2
  };
};
const subregionButtonStyle = (feature: SubregionFeature) => ({
  left: `${(feature.label.x / detailMapSize.width) * 100}%`,
  top: `${(feature.label.y / detailMapSize.height) * 100}%`
});

const issueCopy: Record<string, IssueCard> = {
  GTX: {
    label: '교통 기대',
    detail: 'GTX와 광역 교통망 이슈가 출퇴근 시간 단축 기대와 함께 확산됩니다.',
    risk: '개통 시점 지연과 역 접근성 차이를 분리해서 봐야 합니다.'
  },
  전세: {
    label: '전세 압력',
    detail: '전세 매물 감소 체감과 전세가 방어 여부가 커뮤니티에서 반복됩니다.',
    risk: '실거래 공개 지연 때문에 체감과 신고가를 분리해야 합니다.'
  },
  정비사업: {
    label: '정비사업 기대',
    detail: '재건축·재개발·정비구역 별칭이 늘며 장기 기대가 붙는 흐름입니다.',
    risk: '사업 단계가 낮은 기대 언급은 가격 사실로 보지 않습니다.'
  },
  '대출 규제': {
    label: '정책 민감도',
    detail: '대출 한도와 금리 부담을 두고 관망 댓글이 가격 기대를 압박합니다.',
    risk: '정책 발표 전후로 반응이 급변할 수 있습니다.'
  },
  공급: {
    label: '공급 부담',
    detail: '입주 물량과 매물 누적 체감이 가격 반응을 약하게 만드는 축입니다.',
    risk: '권역 전체보다 생활권 단위로 쪼개서 봐야 합니다.'
  },
  매물: {
    label: '매물 체감',
    detail: '호가와 매물 증가 체감 사이의 간격을 확인해야 하는 구간입니다.',
    risk: '호가·매물 데이터는 출처 계약 전까지 실시간 확인이 필요합니다.'
  },
  교통: {
    label: '교통 이벤트',
    detail: '철도·도로·환승 개선 기대가 특정 생활권 언급량을 바꾸고 있습니다.',
    risk: '발표와 착공, 개통은 시장 반응 강도가 다릅니다.'
  },
  학군: {
    label: '학군 수요',
    detail: '학군·생활 인프라 언급이 전세와 매매 반응을 같이 자극합니다.',
    risk: '계절성과 입학 수요 효과를 분리해야 합니다.'
  },
  '입주 물량': {
    label: '입주 물량',
    detail: '신규 입주는 전세 매물 출회와 함께 체감에 크게 반영됩니다.',
    risk: '입주는 동·단지 단위 확인이 필요합니다.'
  },
  '표본 부족': {
    label: '표본 부족',
    detail: '거래 표본이 얇아 색상보다 stale·confidence 배지를 먼저 봐야 합니다.',
    risk: '작은 변동률을 방향성으로 해석하지 않습니다.'
  }
};
const issueCard = (issue: string): IssueCard =>
  issueCopy[issue] ?? {
    label: issue,
    detail: `${issue} 이슈가 지역 반응의 설명 변수로 관찰됩니다.`,
    risk: '커뮤니티 반응과 시장 fact를 분리해서 확인해야 합니다.'
  };
const selectedIssueCards = computed(() => selectedReport.value?.issues.map(issueCard) ?? []);
const selectedReport = computed(() => {
  if (!selectedRegion.value || !selectedSubregion.value) return null;

  const feature = selectedSubregion.value;
  const target = selectedRegion.value;
  const change = subregionPeriodChange(feature);
  const sampleCount = subregionSampleCount(feature);
  const confidence = subregionConfidence(feature);
  const mentionCount = Math.max(12, Math.round(sampleCount * (1.18 + Math.abs(change) * 0.72)));
  const previousMentionCount = Math.max(7, Math.round(mentionCount / (1.16 + Math.abs(change) * 0.28)));
  const mentionDeltaPct = Math.max(6, Math.round(((mentionCount - previousMentionCount) / previousMentionCount) * 100));
  const primaryIssue = target.issues[0] ?? '지역 반응';
  const secondaryIssue = target.issues[1] ?? '시장 사실';

  return {
    change,
    confidence,
    mentionCount,
    mentionDeltaPct,
    previousMentionCount,
    issues: target.issues,
    metrics: [
      { label: '가격 흐름', value: `${periodLabelById[activePeriod.value]} ${formatChange(change)}` },
      { label: '거래 강도', value: `표본 ${sampleCount}건, ${change > 0 ? '관심 증가' : '관망 우세'}` },
      { label: '전세 압력', value: target.report.jeonsePressure },
      { label: '공급/청약', value: target.report.supplySignal },
      { label: '정책/교통', value: target.report.policyEvent },
      { label: '커뮤니티 언급', value: `언급 ${mentionCount}건, 전 구간 대비 +${mentionDeltaPct}%` }
    ],
    name: `${target.name} ${feature.name}`,
    sampleCount,
    sourceMix: [
      { label: '네이버 카페', value: `${36 + (numberSeed(feature.code) % 9)}%` },
      { label: '지역 블로그', value: `${22 + (numberSeed(feature.code) % 7)}%` },
      { label: '유튜브 댓글', value: `${15 + (numberSeed(feature.code) % 6)}%` },
      { label: '뉴스·정책', value: `${12 + (numberSeed(feature.code) % 5)}%` }
    ],
    summary: `${feature.name}은 ${target.name} 안에서 ${primaryIssue}와 ${secondaryIssue} 이슈가 함께 묶여 관찰되는 하위 지역입니다. 현재 수치는 mock heat layer라 실제 계약·매물 데이터 연결 전까지는 방향성과 표본 신뢰도를 함께 봅니다.`,
    title: change >= 0 ? '언급량 급증' : '우려 언급량 급증',
    bullets: [
      `${feature.name} 관련 언급은 ${previousMentionCount}건에서 ${mentionCount}건으로 늘었습니다.`,
      `${primaryIssue} 키워드가 먼저 움직이고, ${secondaryIssue} 이슈가 댓글 맥락에서 반복됩니다.`,
      `신뢰도 ${confidence}% 기준의 화면용 관찰 요약이며, 공공데이터와 원문 링크 연결 후 확정 지표로 전환됩니다.`
    ],
    previewComplexes: [
      `${feature.name} 대표 생활권`,
      ...(target.sampleComplexes.slice(0, 2) as string[])
    ],
    subregionCode: feature.code,
    subregionName: feature.name
  };
});
const reportPanelStyle = computed(() =>
  reportSettled.value
    ? {
        opacity: '1',
        transform: 'none',
        transition: 'none'
      }
    : undefined
);

const navigateToRegion = (targetId: string) => {
  void router.push(`/realestate/map/${targetId}`);
};
const selectSubregion = (code: string) => {
  selectedSubregionCode.value = code;
  reportSettled.value = false;
  reportOpening.value = true;

  if (reportOpeningTimer) {
    window.clearTimeout(reportOpeningTimer);
  }

  if (reportSettledTimer) {
    window.clearTimeout(reportSettledTimer);
  }

  reportOpeningTimer = window.setTimeout(() => {
    reportOpening.value = false;
  }, 24);

  reportSettledTimer = window.setTimeout(() => {
    reportSettled.value = true;
  }, 280);
};
const closeReport = () => {
  selectedSubregionCode.value = null;
  reportOpening.value = false;
  reportSettled.value = true;

  if (reportOpeningTimer) {
    window.clearTimeout(reportOpeningTimer);
    reportOpeningTimer = undefined;
  }

  if (reportSettledTimer) {
    window.clearTimeout(reportSettledTimer);
    reportSettledTimer = undefined;
  }
};

watch(
  () => route.params.regionId,
  () => {
    closeReport();
  }
);
</script>

<template>
  <section
    :class="['realestate-map-page', { 'has-report': selectedReport, 'is-drilldown': selectedRegion }]"
    aria-labelledby="realestate-map-title"
  >
    <header class="map-page-header">
      <div>
        <p class="eyebrow">regional heat layer · {{ mapFixture.mapDataSource }}</p>
        <h2 id="realestate-map-title">{{ pageTitle }}</h2>
        <p>{{ pageDescription }}</p>
      </div>
      <div class="map-header-actions">
        <RouterLink v-if="selectedRegion" class="map-return-cta" to="/realestate/map" aria-label="전국 지도로 돌아가기">
          <span>←</span>
          <strong>전국 지도로 돌아가기</strong>
        </RouterLink>
        <span class="status-pill warning">mock · {{ mapFixture.asOf }}</span>
        <div class="period-tabs" aria-label="지도 기간 선택">
          <button
            v-for="period in periodOptions"
            :key="period.id"
            type="button"
            :class="{ active: activePeriod === period.id }"
            @click="activePeriod = period.id"
          >
            {{ period.label }}
          </button>
        </div>
      </div>
    </header>

    <section
      :class="['realestate-map-layout', layoutMode]"
      data-testid="realestate-map-layout"
      aria-label="지도와 선택 리포트"
    >
      <article class="realestate-map-stage" aria-labelledby="korea-map-title">
        <div class="map-stage-toolbar">
          <div>
            <p class="label">{{ selectedRegion ? 'municipal drilldown' : 'terrain heatmap' }}</p>
            <h3 id="korea-map-title">
              {{ selectedRegion ? `${selectedRegion.name} Municipal Heat Surface` : 'Korea 3D Market Surface' }}
            </h3>
          </div>
          <div class="map-toolbar-right">
            <RouterLink v-if="selectedRegion" class="map-back-link" to="/realestate/map">← 전국</RouterLink>
            <div class="map-legend" aria-label="지역 색상 범례">
              <span><i class="up"></i>상승</span>
              <span><i class="down"></i>하락</span>
              <span><i class="empty"></i>표본 부족</span>
            </div>
          </div>
        </div>

        <div class="korea-map-shell">
          <div :class="['korea-map-board', { 'region-drilldown-map-board': selectedRegion }]">
            <svg
              v-if="!selectedRegion"
              class="korea-region-map"
              :viewBox="`0 0 ${currentMapSize.width} ${currentMapSize.height}`"
              role="img"
              aria-label="전국 시도별 상승 하락 지도"
            >
              <path class="korea-outline" :d="countryPath" />
              <g class="region-extrusion" aria-hidden="true">
                <path
                  v-for="feature in mapFeatures"
                  :key="`${feature.code}-depth`"
                  :d="feature.path"
                  :transform="feature.pathTransform"
                />
              </g>
              <g class="region-glow-layer" aria-hidden="true">
                <path
                  v-for="feature in mapFeatures"
                  :key="`${feature.code}-glow`"
                  :d="feature.path"
                  :transform="feature.pathTransform"
                  :class="['region-glow', changeTone(periodChange(feature.target))]"
                  :style="{ stroke: heatColor(periodChange(feature.target)) }"
                />
              </g>
              <g>
                <path
                  v-for="feature in mapFeatures"
                  :key="feature.target.id"
                  :d="feature.path"
                  :class="['region-shape', changeTone(periodChange(feature.target))]"
                  :style="{ fill: heatColor(periodChange(feature.target)) }"
                  :transform="feature.pathTransform"
                  :aria-label="`${feature.target.name} ${formatChange(periodChange(feature.target))}`"
                  @click="navigateToRegion(feature.target.id)"
                />
              </g>
              <g class="region-labels" aria-hidden="true">
                <text
                  v-for="feature in mapFeatures"
                  :key="`${feature.target.id}-label`"
                  :x="feature.label.x"
                  :y="feature.label.y"
                >
                  {{ feature.target.name }}
                </text>
              </g>
              <g class="complex-preview-pins" aria-label="단지 좌표 샘플 레이어">
                <circle
                  v-for="feature in samplePins"
                  :key="`${feature.target.id}-pin`"
                  :cx="feature.label.x"
                  :cy="feature.label.y"
                  r="4.5"
                />
              </g>
            </svg>

            <svg
              v-else
              class="korea-region-map subregion-map"
              :viewBox="`0 0 ${currentMapSize.width} ${currentMapSize.height}`"
              role="img"
              :aria-label="`${selectedRegion.name} 구·시·군 상승 하락 지도`"
            >
              <path class="korea-outline region-detail-outline" :d="detailOutlinePath" />
              <g class="region-extrusion" aria-hidden="true">
                <path v-for="feature in subregionFeatures" :key="`${feature.code}-depth`" :d="feature.path" />
              </g>
              <g class="region-glow-layer" aria-hidden="true">
                <path
                  v-for="feature in subregionFeatures"
                  :key="`${feature.code}-glow`"
                  :d="feature.path"
                  :class="['region-glow', changeTone(subregionPeriodChange(feature))]"
                  :style="{ stroke: heatColor(subregionPeriodChange(feature)) }"
                />
              </g>
              <g>
                <path
                  v-for="feature in subregionFeatures"
                  :key="feature.code"
                  :d="feature.path"
                  :class="[
                    'region-shape',
                    'subregion-shape',
                    changeTone(subregionPeriodChange(feature)),
                    { active: selectedSubregion?.code === feature.code }
                  ]"
                  :data-testid="`subregion-shape-${feature.code}`"
                  :style="{ fill: heatColor(subregionPeriodChange(feature)) }"
                  :aria-label="`${feature.name} ${formatChange(subregionPeriodChange(feature))}`"
                  @click="selectSubregion(feature.code)"
                />
              </g>
            </svg>

            <div v-if="!selectedRegion" class="map-target-buttons" aria-label="시도 선택 버튼">
              <button
                v-for="feature in mapFeatures"
                :key="`${feature.target.id}-button`"
                type="button"
                :style="labelButtonStyle(feature)"
                :data-testid="`map-target-${feature.target.id}`"
                :aria-label="`${feature.target.name} ${formatChange(periodChange(feature.target))}`"
                @click="navigateToRegion(feature.target.id)"
              >
                <span>{{ feature.target.name }}</span>
              </button>
            </div>

            <div v-else class="map-target-buttons subregion-target-buttons" aria-label="하위 지역 선택 버튼">
              <button
                v-for="feature in subregionFeatures"
                :key="`${feature.code}-button`"
                type="button"
                :class="{ active: selectedSubregion?.code === feature.code }"
                :style="subregionButtonStyle(feature)"
                :data-testid="`subregion-button-${feature.code}`"
                :aria-label="`${feature.name} ${formatChange(subregionPeriodChange(feature))}`"
                @click="selectSubregion(feature.code)"
              >
                <span>{{ feature.name }}</span>
              </button>
            </div>
          </div>
        </div>

        <div class="map-stage-footer">
          <article>
            <span>{{ selectedRegion ? '가장 강한 하위 지역' : '가장 강한 변동' }}</span>
            <strong>{{ selectedRegion ? strongestSubregion?.name : strongestRegion.name }}</strong>
            <em
              :class="
                selectedRegion && strongestSubregion
                  ? changeTone(subregionPeriodChange(strongestSubregion))
                  : changeTone(periodChange(strongestRegion))
              "
            >
              {{
                selectedRegion && strongestSubregion
                  ? formatChange(subregionPeriodChange(strongestSubregion))
                  : formatChange(periodChange(strongestRegion))
              }}
            </em>
          </article>
          <article>
            <span>{{ selectedRegion ? '하위 지역' : '지역 단위' }}</span>
            <strong>{{ selectedRegion ? `${subregionFeatures.length}개 구·시·군` : '17개 시도' }}</strong>
            <em>{{ selectedRegion ? '실제 시군구 경계' : 'GeoJSON 교체 가능' }}</em>
          </article>
          <article>
            <span>다음 단계</span>
            <strong>{{ selectedRegion ? '단지 좌표 매핑' : '시군구 drilldown' }}</strong>
            <em>{{ selectedRegion ? '아파트 상세 연결 후보' : '지역 클릭으로 진입' }}</em>
          </article>
        </div>
      </article>

      <aside
        v-if="selectedReport"
        :class="['map-report-panel', { opening: reportOpening }]"
        :style="reportPanelStyle"
        data-testid="map-report-panel"
        aria-labelledby="map-report-title"
      >
        <div class="map-report-header">
          <div>
            <p class="label">지역 리포트</p>
            <h3 id="map-report-title">{{ selectedReport.name }}</h3>
            <span>{{ selectedRegion?.regionCode }} · {{ selectedReport.subregionCode }}</span>
          </div>
          <button class="icon-button" data-testid="close-map-report" type="button" aria-label="지역 리포트 닫기" @click="closeReport">
            ×
          </button>
        </div>

        <div class="report-lead">
          <strong :class="changeTone(selectedReport.change)">{{ formatChange(selectedReport.change) }}</strong>
          <p>{{ selectedReport.summary }}</p>
          <div>
            <span class="status-pill subtle">표본 {{ selectedReport.sampleCount }}건</span>
            <span class="status-pill subtle">신뢰도 {{ selectedReport.confidence }}%</span>
          </div>
        </div>

        <section class="community-pulse-board" aria-labelledby="community-pulse-title">
          <div class="report-section-title">
            <p class="label">community pulse</p>
            <h4 id="community-pulse-title">{{ selectedReport.title }}</h4>
          </div>
          <div class="mention-delta-card">
            <strong>+{{ selectedReport.mentionDeltaPct }}%</strong>
            <span>{{ selectedReport.previousMentionCount }}건 → {{ selectedReport.mentionCount }}건</span>
            <p>{{ selectedReport.subregionName }} 관련 커뮤니티 언급이 선택 기간에 빠르게 늘었습니다.</p>
          </div>
          <div class="community-source-mix">
            <article v-for="source in selectedReport.sourceMix" :key="source.label">
              <span>{{ source.label }}</span>
              <strong>{{ source.value }}</strong>
            </article>
          </div>
          <ul class="community-bullet-list">
            <li v-for="bullet in selectedReport.bullets" :key="bullet">{{ bullet }}</li>
          </ul>
        </section>

        <section class="issue-report-section" aria-labelledby="issue-report-title">
          <div class="report-section-title">
            <p class="label">issue matrix</p>
            <h4 id="issue-report-title">핵심 쟁점</h4>
          </div>
          <div class="issue-card-grid">
            <article v-for="issue in selectedIssueCards" :key="issue.label">
              <span>{{ issue.label }}</span>
              <strong>{{ issue.detail }}</strong>
              <em>{{ issue.risk }}</em>
            </article>
          </div>
        </section>

        <div class="report-metric-grid">
          <article v-for="metric in selectedReport.metrics" :key="metric.label">
            <span>{{ metric.label }}</span>
            <strong>{{ metric.value }}</strong>
          </article>
        </div>

        <section class="report-chip-section" aria-label="주요 쟁점">
          <span v-for="issue in selectedReport.issues" :key="issue">{{ issue }}</span>
        </section>

        <section class="sample-complex-list" aria-labelledby="sample-complex-title">
          <div class="section-band-title compact">
            <p class="label">complex preview</p>
            <h4 id="sample-complex-title">다음 연결 후보</h4>
          </div>
          <article v-for="complex in selectedReport.previewComplexes" :key="complex">
            <strong>{{ complex }}</strong>
            <span>좌표·별칭 매핑 후 단지 리포트로 연결</span>
          </article>
        </section>
      </aside>
    </section>
  </section>
</template>
