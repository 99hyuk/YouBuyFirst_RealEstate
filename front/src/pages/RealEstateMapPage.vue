<script setup lang="ts">
import { geoContains, geoMercator, geoPath } from 'd3-geo';
import type { Feature, FeatureCollection, GeoJsonProperties, Geometry, Position } from 'geojson';
import { feature as topojsonFeature } from 'topojson-client';
import type { GeometryCollection, Topology } from 'topojson-specification';
import { computed, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import mapFixture from '../fixtures/realestate-map-targets.json';
import transactionRegionData from '../fixtures/transaction-regions.json';
import municipalityTopologyUrl from '../fixtures/skorea-municipalities-2018-topo-simple.json?url';
import koreaProvincesTopo from '../fixtures/skorea-provinces-2018-topo-simple.json';
import {
  buildMapHeatScale,
  fetchRealEstateMapLayer,
  mapHeatColor,
  mapHeatTone,
  type PeriodKey,
  type RealEstateMapLayerPeriod,
  type RealEstateMapLayerResponse,
  type RealEstateMapLayerTarget
} from '../lib/realestate-map';
import {
  subscribeRealEstateBatchUpdates,
  type BatchUpdateSubscription
} from '../lib/realestate-batch-updates';
import {
  fetchRealEstateTargetEvidenceLogs,
  type RealEstateEvidenceItem,
  type RealEstateEvidenceLog
} from '../lib/realestate-evidence-logs';
import {
  fetchRealEstateRegionalReport,
  type RealEstateRegionalReport
} from '../lib/realestate-regional-reports';
import { currentAuthUser } from '../lib/auth-session';
import { recordRecentRealEstateView } from '../lib/realestate-recent-views';
import {
  isUserWatchTargetSaved,
  loadUserWatchTargets,
  removeUserWatchTarget,
  safeWatchTargetTestId,
  saveUserWatchTarget,
  type UserWatchTargetPayload
} from '../lib/user-watch-targets';

type ReportKey =
  | 'priceFlow'
  | 'tradeStrength'
  | 'jeonsePressure'
  | 'supplySignal'
  | 'policyEvent'
  | 'communityReaction';
type FixtureMapTarget = (typeof mapFixture.targets)[number];
type MapTarget = FixtureMapTarget & {
  asOf?: string | null;
  dataStatus?: string | null;
  layerPeriods?: Partial<Record<PeriodKey, RealEstateMapLayerPeriod>>;
  periodChanges: Partial<Record<PeriodKey, number>>;
  provider?: string | null;
  sourceLabel?: string | null;
  stale?: boolean;
  targetId: string;
};
type ChatAttachmentPayload = {
  type: 'region' | 'complex';
  targetId: string;
  title: string;
  subtitle: string;
  metricLabel?: string;
  metricValue?: string;
  metricTone?: 'up' | 'down' | 'flat';
  landingPath: string;
};
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
type ReportAnalysisSegment = {
  key: string;
  label: '평가' | '전망' | null;
  text: string;
};
type MapFeature = {
  code: string;
  depthTransform: string;
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
type SubregionCluster = {
  availableCount: number;
  center: { x: number; y: number };
  count: number;
  id: string;
  label: string;
};
const route = useRoute();
const router = useRouter();

const periodOptions: { id: PeriodKey; label: string }[] = [
  { id: 'week', label: '1주' },
  { id: 'month', label: '1개월' },
  { id: 'quarter', label: '3개월' },
  { id: 'halfYear', label: '6개월' },
  { id: 'year', label: '1년' }
];
const periodLabelById: Record<PeriodKey, string> = {
  week: '최근 1주',
  month: '최근 1개월',
  quarter: '최근 3개월',
  halfYear: '최근 6개월',
  year: '최근 1년'
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
const activePeriodIndex = computed(() => Math.max(0, periodOptions.findIndex((period) => period.id === activePeriod.value)));
const periodSliderStyle = computed<Record<string, string>>(() => ({
  '--period-active-index': String(activePeriodIndex.value),
  '--period-count': String(periodOptions.length)
}));
const selectedSubregionCode = ref<string | null>(null);
const selectedSubregionClusterId = ref<string | null>(null);
const reportOpening = ref(false);
const reportSettled = ref(true);
let reportOpeningTimer: number | undefined;
let reportSettledTimer: number | undefined;
let batchUpdateSubscription: BatchUpdateSubscription | null = null;

const targets = reactive<MapTarget[]>(
  mapFixture.targets.map((target) => ({
    ...target,
    dataStatus: 'mock',
    stale: true,
    targetId: target.targetId
  }))
);
const hoveredRegionCode = ref<string | null>(null);
const mapLayerLoadState = ref<'loading' | 'live' | 'fallback'>('loading');
const subregionLayerLoadState = ref<'idle' | 'loading' | 'live' | 'fallback'>('idle');
const subregionLayerByCode = shallowRef<Map<string, RealEstateMapLayerTarget>>(new Map());
const mapEvidenceLogs = ref<RealEstateEvidenceLog[]>([]);
const mapEvidenceLoadState = ref<'idle' | 'loading' | 'live' | 'empty' | 'error'>('idle');
const regionalReport = ref<RealEstateRegionalReport | null>(null);
const regionalReportLoadState = ref<'idle' | 'loading' | 'live' | 'empty' | 'error'>('idle');
const mapLayerMeta = reactive({
  asOf: mapFixture.asOf as string | null,
  dataStatus: 'mock' as string | null,
  mapDataSource: mapFixture.mapDataSource as string | null,
  sourceLabel: mapFixture.sourceLabel as string | null,
  stale: true
});
const nationalMapSize = { width: 430, height: 630 };
const detailMapSize = { width: 560, height: 560 };
const detailExtrusionTransform = 'translate(0 7)';
const currentMapSize = computed(() => (selectedRegion.value ? detailMapSize : nationalMapSize));
const minMapZoom = 1;
const maxMapZoom = 3.2;
const clusteredSubregionRegionCodes = new Set(['31']);
const parentOnlyReportTargetIds = new Set(['region-sejong']);
const gyeonggiSubregionClusterByCode: Record<string, 'center' | 'north' | 'south' | 'west'> = {
  '31011': 'center',
  '31012': 'center',
  '31013': 'center',
  '31014': 'center',
  '31021': 'center',
  '31022': 'center',
  '31023': 'center',
  '31030': 'north',
  '31041': 'center',
  '31042': 'center',
  '31050': 'west',
  '31060': 'west',
  '31070': 'south',
  '31080': 'north',
  '31091': 'west',
  '31092': 'west',
  '31101': 'north',
  '31103': 'north',
  '31104': 'north',
  '31110': 'center',
  '31120': 'center',
  '31130': 'center',
  '31140': 'south',
  '31150': 'west',
  '31160': 'center',
  '31170': 'center',
  '31180': 'center',
  '31191': 'south',
  '31192': 'south',
  '31193': 'south',
  '31200': 'north',
  '31210': 'south',
  '31220': 'south',
  '31230': 'west',
  '31240': 'south',
  '31250': 'center',
  '31260': 'north',
  '31270': 'north',
  '31280': 'south',
  '31350': 'north',
  '31370': 'center',
  '31380': 'center'
};
const mapViewport = reactive({
  dragMoved: false,
  isDragging: false,
  lastX: 0,
  lastY: 0,
  panX: 0,
  panY: 0,
  scale: 1,
  suppressClick: false
});
const isMapZoomed = computed(
  () => mapViewport.scale > minMapZoom + 0.01 || Math.abs(mapViewport.panX) > 1 || Math.abs(mapViewport.panY) > 1
);
const mapZoomPercent = computed(() => `${Math.round(mapViewport.scale * 100)}%`);
const mapBoardStyle = computed(() => ({
  '--map-label-scale': (1 / Math.max(mapViewport.scale, 1)).toFixed(3),
  '--map-pan-x': `${mapViewport.panX.toFixed(1)}px`,
  '--map-pan-y': `${mapViewport.panY.toFixed(1)}px`,
  '--map-zoom': mapViewport.scale.toFixed(3)
}));

const koreaTopology = koreaProvincesTopo as KoreaTopology;
const provinceFeatureCollection = topojsonFeature(
  koreaTopology,
  koreaTopology.objects.skorea_provinces_2018_geo
) as FeatureCollection<Geometry, ProvinceProperties>;

const polygonArea = (ring: Position[]) => {
  if (ring.length < 3) return 0;

  return Math.abs(
    ring.reduce((sum, point, index) => {
      const previous = ring[index === 0 ? ring.length - 1 : index - 1];

      return sum + (previous[0] * point[1] - point[0] * previous[1]);
    }, 0) / 2
  );
};

const polygonLongitudeBounds = (polygon: Position[][]) =>
  polygon.flat().reduce(
    (bounds, point) => ({
      maxX: Math.max(bounds.maxX, point[0]),
      minX: Math.min(bounds.minX, point[0])
    }),
    { maxX: Number.NEGATIVE_INFINITY, minX: Number.POSITIVE_INFINITY }
  );

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

const incheonRemoteOffshoreLongitude = 126.2;
const omitRemoteIncheonOffshorePolygons = (
  feature: MunicipalityFeature
): MunicipalityFeature => {
  if (feature.properties.code !== '23320' || feature.geometry.type !== 'MultiPolygon') return feature;

  const visiblePolygons = feature.geometry.coordinates.filter(
    (polygon) => polygonLongitudeBounds(polygon).maxX >= incheonRemoteOffshoreLongitude
  );

  if (!visiblePolygons.length) return feature;

  return {
    ...feature,
    geometry: {
      ...feature.geometry,
      coordinates: visiblePolygons
    }
  };
};

const gyeongbukUlleungCode = '37430';
const gyeongbukUlleungInsetOffset = { lat: -0.58, lon: -1.18 };
const shiftGyeongbukUlleungPosition = (position: Position): Position => [
  position[0] + gyeongbukUlleungInsetOffset.lon,
  position[1] + gyeongbukUlleungInsetOffset.lat,
  ...position.slice(2)
];
const repositionGyeongbukUlleungInset = (feature: MunicipalityFeature): MunicipalityFeature => {
  if (feature.properties.code !== gyeongbukUlleungCode) return feature;

  if (feature.geometry.type === 'Polygon') {
    return {
      ...feature,
      geometry: {
        ...feature.geometry,
        coordinates: feature.geometry.coordinates.map((ring) => ring.map(shiftGyeongbukUlleungPosition))
      }
    };
  }

  if (feature.geometry.type === 'MultiPolygon') {
    return {
      ...feature,
      geometry: {
        ...feature.geometry,
        coordinates: feature.geometry.coordinates.map((polygon) =>
          polygon.map((ring) => ring.map(shiftGyeongbukUlleungPosition))
        )
      }
    };
  }

  return feature;
};

const projectedInteriorPoint = (
  feature: Feature<Geometry, GeoJsonProperties>,
  projection: ReturnType<typeof geoMercator>,
  pathGenerator: ReturnType<typeof geoPath>
) => {
  const centroid = pathGenerator.centroid(feature);
  const projectedToCoordinates = projection.invert?.(centroid);

  if (projectedToCoordinates && geoContains(feature, projectedToCoordinates)) {
    return centroid;
  }

  const [[minX, minY], [maxX, maxY]] = pathGenerator.bounds(feature);
  const center = [(minX + maxX) / 2, (minY + maxY) / 2];
  const steps = 28;
  let bestPoint = centroid;
  let bestScore = Number.POSITIVE_INFINITY;

  for (let yIndex = 0; yIndex <= steps; yIndex += 1) {
    for (let xIndex = 0; xIndex <= steps; xIndex += 1) {
      const point: [number, number] = [
        minX + ((maxX - minX) * xIndex) / steps,
        minY + ((maxY - minY) * yIndex) / steps
      ];
      const coordinates = projection.invert?.(point);

      if (!coordinates || !geoContains(feature, coordinates)) continue;

      const score = (point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2;

      if (score < bestScore) {
        bestPoint = point;
        bestScore = score;
      }
    }
  }

  return bestPoint;
};

const provinceDisplayCollection: FeatureCollection<Geometry, ProvinceProperties> = {
  ...provinceFeatureCollection,
  features: provinceFeatureCollection.features.map((feature) => trimSmallMultipolygons(feature as ProvinceFeature, 0.04))
};
const countryOutlineFeatureCollection: FeatureCollection<Geometry, ProvinceProperties> = {
  ...provinceDisplayCollection,
  features: provinceDisplayCollection.features.filter((feature) => feature.properties.code !== '39')
};
const emptyMunicipalityFeatureCollection: FeatureCollection<Geometry, MunicipalityProperties> = {
  type: 'FeatureCollection',
  features: []
};
const municipalityFeatureCollection = shallowRef<FeatureCollection<Geometry, MunicipalityProperties>>(
  emptyMunicipalityFeatureCollection
);
const municipalityLoadState = ref<'idle' | 'loading' | 'loaded' | 'error'>('idle');
let municipalityLoadPromise: Promise<void> | null = null;
const targetByRegionCode = new Map(targets.map((target) => [target.regionCode, target]));
const targetByRouteId = computed(() => {
  const entries = new Map<string, MapTarget>();
  for (const target of targets) {
    entries.set(target.id.toLowerCase(), target);
    entries.set(target.targetId.toLowerCase(), target);
  }
  return entries;
});
const nationalProjection = geoMercator().fitSize([nationalMapSize.width, nationalMapSize.height], provinceDisplayCollection);
const nationalPathGenerator = geoPath(nationalProjection);
const countryPath = nationalPathGenerator(countryOutlineFeatureCollection) ?? '';
const mapFeatures = provinceDisplayCollection.features.reduce<MapFeature[]>((items, feature: ProvinceFeature) => {
  const target = targetByRegionCode.get(feature.properties.code);
  const path = nationalPathGenerator(feature);
  const centroid = projectedInteriorPoint(feature, nationalProjection, nationalPathGenerator);

  if (!target || !path || !Number.isFinite(centroid[0]) || !Number.isFinite(centroid[1])) return items;

  const visualOffsetY = target.id === 'jeju' ? -56 : 0;

  items.push({
    code: feature.properties.code,
    depthTransform: `translate(0 ${visualOffsetY + 13})`,
    label: { x: centroid[0], y: centroid[1] + visualOffsetY },
    path,
    pathTransform: visualOffsetY ? `translate(0 ${visualOffsetY})` : undefined,
    provinceName: feature.properties.name,
    target
  });

  return items;
}, []);
const samplePins = computed(() => mapFeatures.filter((feature) => feature.target.sampleCount > 0).slice(0, 8));
const labelNudgeByRegionId: Record<string, { x: number; y: number }> = {
  chungbuk: { x: -8, y: -4 },
  gyeonggi: { x: 0, y: 36 }
};

const routeRegionId = computed(() => String(route.params.regionId ?? '').toLowerCase());
const queryStringValue = (value: unknown) => {
  const firstValue = Array.isArray(value) ? value[0] : value;
  return typeof firstValue === 'string' ? firstValue : '';
};
const routeSelectedTargetId = computed(() => queryStringValue(route.query.selectedTargetId));
const routeSelectedRegionCode = computed(() => queryStringValue(route.query.selectedRegionCode));
const routeSelectedPeriod = computed<PeriodKey | null>(() => {
  const period = queryStringValue(route.query.period) as PeriodKey;
  return periodOptions.some((option) => option.id === period) ? period : null;
});
const selectedRegion = computed(() => targetByRouteId.value.get(routeRegionId.value) ?? null);
const layoutMode = computed(() => (selectedReport.value ? 'split' : 'centered'));
const pageTitle = computed(() => (selectedRegion.value ? `${selectedRegion.value.name} 상세 흐름 지도` : '전국 지역 흐름 지도'));
const pageDescription = computed(() =>
  selectedRegion.value
    ? `${selectedRegion.value.name} 안의 구·시·군 가격 흐름을 행정구역 경계 위에서 확인합니다.`
    : '전국 시도별 가격 흐름을 3D 지도 위에서 확인하고, 지역을 누르면 시군구 상세 지도로 이동합니다.'
);

const loadMunicipalityTopology = () => {
  if (municipalityLoadState.value === 'loaded') return Promise.resolve();
  if (municipalityLoadPromise) return municipalityLoadPromise;

  municipalityLoadState.value = 'loading';
  municipalityLoadPromise = fetch(municipalityTopologyUrl)
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`Municipality topology request failed: ${response.status}`);
      }

      return (await response.json()) as MunicipalityTopology;
    })
    .then((municipalityTopology) => {
      municipalityFeatureCollection.value = topojsonFeature(
        municipalityTopology,
        municipalityTopology.objects.skorea_municipalities_2018_geo
      ) as FeatureCollection<Geometry, MunicipalityProperties>;
      municipalityLoadState.value = 'loaded';
    })
    .catch(() => {
      municipalityFeatureCollection.value = emptyMunicipalityFeatureCollection;
      municipalityLoadState.value = 'error';
    })
    .finally(() => {
      municipalityLoadPromise = null;
    });

  return municipalityLoadPromise;
};

const selectedMunicipalityBaseCollection = computed<FeatureCollection<Geometry, MunicipalityProperties>>(() => {
  if (!selectedRegion.value) {
    return {
      type: 'FeatureCollection',
      features: []
    };
  }

  return {
    type: 'FeatureCollection',
    features: municipalityFeatureCollection.value.features
      .filter((feature) => feature.properties.code.startsWith(selectedRegion.value!.regionCode))
      .map((feature) => trimSmallMultipolygons(feature as MunicipalityFeature, 0.04) as MunicipalityFeature)
      .map((feature) => selectedRegion.value!.regionCode === '23'
        ? omitRemoteIncheonOffshorePolygons(feature)
        : feature)
      .map((feature) => selectedRegion.value!.regionCode === '37'
        ? repositionGyeongbukUlleungInset(feature)
        : feature)
  };
});
const selectedMunicipalityCollection = computed<FeatureCollection<Geometry, MunicipalityProperties>>(() => {
  const baseCollection = selectedMunicipalityBaseCollection.value;
  if (!selectedSubregionClusterId.value || !isClusteredSubregionMap.value) return baseCollection;

  return {
    type: 'FeatureCollection',
    features: baseCollection.features.filter(
      (feature) => subregionClusterIdByCode(feature.properties.code) === selectedSubregionClusterId.value
    )
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
    const label = projectedInteriorPoint(feature, detailProjection.value, detailPathGenerator.value);

    if (!path || !label) return items;

    items.push({
      code: feature.properties.code,
      label: { x: label[0], y: label[1] },
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
// 실거래 지도 정보 제공 지역 화이트리스트. 지도 토폴로지 코드가 실거래 legalDongCode와
// 달라(예: 강남구 토폴로지 11230 ≠ 실거래 11680) 코드가 아닌 '시도|시군구명'으로 매칭한다.
const transactionRegionByName = new Map<string, string>();
const transactionSidoFirstCode = new Map<string, string>();
for (const group of transactionRegionData.groups as { sido: string; items: { code: string; name: string }[] }[]) {
  for (const item of group.items) {
    const district = item.name.split(' ').pop() ?? item.name;
    transactionRegionByName.set(`${group.sido}|${district}`, item.code);
    if (!transactionSidoFirstCode.has(group.sido)) transactionSidoFirstCode.set(group.sido, item.code);
  }
}
// 선택한 지역의 실거래 대상 코드: 시군구가 화이트리스트에 있으면 그 코드(legalDongCode),
// 시도만 선택했으면 해당 시도의 첫 화이트리스트 시군구, 아니면 null(정보 없음).
const transactionTargetCode = computed<string | null>(() => {
  const sido = selectedRegion.value?.name;
  if (!sido) return null;
  if (selectedSubregion.value) {
    return transactionRegionByName.get(`${sido}|${selectedSubregion.value.name}`) ?? null;
  }
  return transactionSidoFirstCode.get(sido) ?? null;
});
const hasTransactionData = computed(() => transactionTargetCode.value !== null);
const transactionMapLink = computed(() =>
  transactionTargetCode.value ? `/realestate/transactions?region=${transactionTargetCode.value}` : ''
);
const transactionMapLabel = computed(() => {
  const regionLabel = selectedSubregion.value?.name ?? selectedRegion.value?.name ?? '';
  return hasTransactionData.value ? `${regionLabel} 실거래 지도` : '실거래 정보 없음';
});
const targetPeriodChangeValue = (target: MapTarget, period: PeriodKey = activePeriod.value) =>
  target.periodChanges[period] ?? 0;
const highestGainRegion = computed(() =>
  [...targets].sort(
    (left, right) => targetPeriodChangeValue(right) - targetPeriodChangeValue(left)
  )[0]
);
const largestDeclineRegion = computed(() =>
  [...targets].sort(
    (left, right) => targetPeriodChangeValue(left) - targetPeriodChangeValue(right)
  )[0]
);
const strongestRegion = computed(() =>
  [...targets].sort(
    (left, right) => Math.abs(targetPeriodChangeValue(right)) - Math.abs(targetPeriodChangeValue(left))
  )[0]
);

const targetPeriodMeta = (target: MapTarget, period: PeriodKey = activePeriod.value) => target.layerPeriods?.[period] ?? null;
const usableMapPeriod = (period?: RealEstateMapLayerPeriod | null) => {
  if (!period) return null;
  const status = (period.dataStatus ?? '').toLowerCase();
  const provider = (period.provider ?? '').toLowerCase();
  if (
    status === 'mock'
    || status === 'empty'
    || provider === 'seed'
    || provider === 'real_estate_reaction_snapshots'
    || provider === 'reaction_snapshots'
  ) return null;
  return period;
};
const periodChange = (target: MapTarget) => usableMapPeriod(targetPeriodMeta(target))?.changePct ?? 0;
const targetSampleCount = (target: MapTarget) => usableMapPeriod(targetPeriodMeta(target))?.sampleCount ?? 0;
const targetConfidence = (target: MapTarget) => usableMapPeriod(targetPeriodMeta(target))?.confidence ?? 0;
const subregionLayerTargetForFeature = (feature: SubregionFeature) =>
  subregionLayerByCode.value.get(feature.code) ?? null;
const subregionLayerPeriod = (feature: SubregionFeature, period: PeriodKey = activePeriod.value) =>
  subregionLayerTargetForFeature(feature)?.periods?.[period] ?? null;
const effectiveSubregionPeriod = (feature: SubregionFeature, period: PeriodKey = activePeriod.value) =>
  usableMapPeriod(subregionLayerPeriod(feature, period));
const hasSubregionPeriod = (feature: SubregionFeature, period: PeriodKey = activePeriod.value) =>
  Boolean(effectiveSubregionPeriod(feature, period));
const isSubregionUnavailable = (feature: SubregionFeature) => !hasSubregionPeriod(feature);
const formatChange = (value: number) => `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
const confidencePercent = (value?: number | null) => {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 0;
  return Math.round(value <= 1 ? value * 100 : value);
};
const formatEvidenceConfidence = (value?: number | null) => `${confidencePercent(value)}%`;
const formatMapTimestamp = (value?: string | null) => {
  if (!value) return '기준 시각 확인 필요';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  return `${new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(parsed)} KST`;
};
const formatMapUpdateDate = (value?: string | null) => {
  if (!value) return '확인 필요';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  return new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(parsed).replace(/\.\s?/g, '.').replace(/\.$/, '');
};
const mapEvidenceQualityLabel = (quality?: string | null) => mapDataStatusLabel(quality);
const displayMapEvidenceCopy = (text?: string | null) =>
  (text ?? '')
    .replace(/\bEvidenceLog\b/g, '근거 로그')
    .replace(/\bsnapshot\b/gi, '집계 자료')
    .replace(/\bSerpApi\b/g, '최근 이슈 검색')
    .replace(/\bGMS\b/g, 'AI')
    .replace(/\bAPI\b/g, '데이터 연동')
    .replace(/\basOf\b/g, '기준 시각')
    .replace(/\bnational_market_fact_only\b/g, '전국 지표만 반영')
    .replace(/\bsimilar_window_missing\b/g, '유사 과거 미연결')
    .replace(/\bmarket_fact_missing\b/g, '시장 사실 미연결')
    .replace(/\bsearch_candidate_missing\b/g, '최근 이슈 후보 미연결')
    .replace(/\bllm_evaluation_failed\b/g, 'AI 요약 보강 지연')
    .replace(/\bpartial\b/g, '일부 데이터 기반')
    .replace(/\blow_sample\b/g, '표본 부족')
    .replace(/\bsource_skewed\b/g, '출처 편중')
    .replace(/\bstale\b/g, '갱신 지연');
const changeTone = (value: number) => mapHeatTone(value);
const mapDataStatusLabel = (status?: string | null) => {
  const normalized = (status ?? '').toLowerCase();
  if (normalized === 'ok') return '공공데이터 반영';
  if (normalized === 'partial') return '부분 반영';
  if (normalized === 'insufficient') return '수집 전';
  if (normalized === 'empty') return '데이터 없음';
  if (normalized === 'mock') return '수집 전';
  if (normalized === 'low_sample') return '표본 부족';
  if (normalized === 'unknown' || !normalized) return '확인 필요';
  return status ?? '확인 필요';
};
const mapSourceLabel = (source?: string | null) => {
  const normalized = source?.trim();
  if (!normalized) return '출처 확인 필요';
  const labels: Record<string, string> = {
    reb: '한국부동산원 R-ONE',
    reb_rone_regional_price_change: '한국부동산원 R-ONE 지역 가격지표',
    real_estate_reaction_snapshots: '반응 지표',
    reaction_snapshots: '반응 지표',
    parent_reaction_snapshot: '상위 지역 반응',
    map_layer_snapshots: '지도 흐름 자료',
    market_facts: '시장 사실',
    molit: '국토교통부',
    reb_stat: '한국부동산원'
  };
  return labels[normalized] ?? normalized.replace(/_/g, ' ');
};
const unpublishedHeatColor = 'rgba(10, 15, 24, 0.82)';
const unpublishedGlowColor = 'rgba(4, 8, 14, 0.72)';
const missingHeatColor = 'rgba(126, 143, 166, 0.18)';
const nationalHeatScale = computed(() =>
  buildMapHeatScale(
    mapFeatures
      .map((feature) => usableMapPeriod(targetPeriodMeta(feature.target))?.changePct)
      .filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
  )
);
const selectedRegionHeatBaseline = computed(() =>
  selectedRegion.value ? usableMapPeriod(targetPeriodMeta(selectedRegion.value))?.changePct : undefined
);
const subregionHeatScale = computed(() =>
  buildMapHeatScale(
    subregionFeatures.value
      .map((feature) => effectiveSubregionPeriod(feature)?.changePct)
      .filter((value): value is number => typeof value === 'number' && Number.isFinite(value)),
    selectedRegionHeatBaseline.value
  )
);
const nationalRegionHeatColor = (target: MapTarget) => {
  const period = usableMapPeriod(targetPeriodMeta(target));
  return period ? mapHeatColor(period.changePct, nationalHeatScale.value) : missingHeatColor;
};
const subregionPeriodChange = (feature: SubregionFeature, period: PeriodKey = activePeriod.value) => {
  const livePeriod = effectiveSubregionPeriod(feature, period);
  if (livePeriod) return livePeriod.changePct;
  return 0;
};
const subregionFeaturesWithPeriod = computed(() =>
  subregionFeatures.value.filter((feature) => hasSubregionPeriod(feature))
);
const highestGainSubregion = computed(() =>
  [...subregionFeaturesWithPeriod.value].sort(
    (left, right) =>
      subregionPeriodChange(right, activePeriod.value) - subregionPeriodChange(left, activePeriod.value)
  )[0] ?? null
);
const largestDeclineSubregion = computed(() =>
  [...subregionFeaturesWithPeriod.value].sort(
    (left, right) =>
      subregionPeriodChange(left, activePeriod.value) - subregionPeriodChange(right, activePeriod.value)
  )[0] ?? null
);
const strongestSubregion = computed(() =>
  [...subregionFeaturesWithPeriod.value].sort(
    (left, right) =>
      Math.abs(subregionPeriodChange(right, activePeriod.value)) - Math.abs(subregionPeriodChange(left, activePeriod.value))
  )[0] ?? null
);
const subregionSampleCount = (feature: SubregionFeature) => {
  const livePeriod = effectiveSubregionPeriod(feature);
  if (livePeriod) return livePeriod.sampleCount;
  return 0;
};
const subregionConfidence = (feature: SubregionFeature) =>
  effectiveSubregionPeriod(feature)?.confidence ?? 0;
const mapTransformOrigin = { x: 50, y: 54 };
const mapLabelPositionStyle = (
  point: { x: number; y: number },
  size: { height: number; width: number }
) => {
  const leftPct = (point.x / size.width) * 100;
  const topPct = (point.y / size.height) * 100;

  if (!isMapZoomed.value) {
    return {
      left: `${leftPct}%`,
      top: `${topPct}%`
    };
  }

  const zoom = Math.max(mapViewport.scale, 1);
  const zoomedLeftPct = mapTransformOrigin.x + (leftPct - mapTransformOrigin.x) * zoom;
  const zoomedTopPct = mapTransformOrigin.y + (topPct - mapTransformOrigin.y) * zoom;

  return {
    left: `calc(${zoomedLeftPct.toFixed(3)}% + ${mapViewport.panX.toFixed(1)}px)`,
    top: `calc(${zoomedTopPct.toFixed(3)}% + ${mapViewport.panY.toFixed(1)}px)`
  };
};
const labelButtonStyle = (feature: MapFeature) => mapLabelPositionStyle({
  x: feature.label.x + (labelNudgeByRegionId[feature.target.id]?.x ?? 0),
  y: feature.label.y + (labelNudgeByRegionId[feature.target.id]?.y ?? 0)
}, nationalMapSize);
const subregionButtonStyle = (feature: SubregionFeature) => mapLabelPositionStyle(feature.label, detailMapSize);
const shortRegionName = (name: string) =>
  name
    .replace(/특별자치도$/, '')
    .replace(/특별시$/, '')
    .replace(/광역시$/, '')
    .replace(/도$/, '');
function subregionClusterIdByCode(code: string): string | null {
  if (code.startsWith('31')) return gyeonggiSubregionClusterByCode[code] ?? 'center';
  return null;
}
const subregionClusterId = (feature: SubregionFeature) => {
  const codeClusterId = subregionClusterIdByCode(feature.code);
  if (codeClusterId) return codeClusterId;

  const xRatio = feature.label.x / detailMapSize.width;
  const yRatio = feature.label.y / detailMapSize.height;

  if (yRatio < 0.34) return 'north';
  if (yRatio > 0.66) return 'south';
  if (xRatio < 0.42) return 'west';
  if (xRatio > 0.62) return 'east';
  return 'center';
};
const subregionClusterLabelById: Record<string, string> = {
  center: '중부',
  north: '북부',
  south: '남부',
  west: '서부'
};
const subregionClusterNudgeById: Record<string, { x: number; y: number }> = {
  center: { x: 26, y: 0 }
};
const isClusteredSubregionMap = computed(() =>
  Boolean(selectedRegion.value && clusteredSubregionRegionCodes.has(selectedRegion.value.regionCode))
);
const focusedSubregionClusterLabel = computed(() => {
  if (!selectedRegion.value || !selectedSubregionClusterId.value) return null;
  const regionName = shortRegionName(selectedRegion.value.name);
  const clusterName = subregionClusterLabelById[selectedSubregionClusterId.value] ?? '권역';
  return `${regionName} ${clusterName}`;
});
const showSubregionClusters = computed(
  () => isClusteredSubregionMap.value && !selectedSubregion.value && !selectedSubregionClusterId.value
);
const subregionClusters = computed<SubregionCluster[]>(() => {
  if (!selectedRegion.value || !isClusteredSubregionMap.value) return [];

  const groups = subregionFeatures.value.reduce<Map<string, SubregionFeature[]>>((entries, feature) => {
    const id = subregionClusterId(feature);
    entries.set(id, [...(entries.get(id) ?? []), feature]);
    return entries;
  }, new Map());
  const regionName = shortRegionName(selectedRegion.value.name);

  return [...groups.entries()]
    .map(([id, features]) => {
      const center = features.reduce(
        (point, feature) => ({
          x: point.x + feature.label.x / features.length,
          y: point.y + feature.label.y / features.length
        }),
        { x: 0, y: 0 }
      );

      return {
        availableCount: features.filter((feature) => hasSubregionPeriod(feature)).length,
        center,
        count: features.length,
        id,
        label: `${regionName} ${subregionClusterLabelById[id] ?? '권역'}`
      };
    })
    .sort((left, right) => left.center.y - right.center.y || left.center.x - right.center.x);
});
const subregionClusterButtonStyle = (cluster: SubregionCluster) => mapLabelPositionStyle({
  x: cluster.center.x + (subregionClusterNudgeById[cluster.id]?.x ?? 0),
  y: cluster.center.y + (subregionClusterNudgeById[cluster.id]?.y ?? 0)
}, detailMapSize);
const firstPeriod = (periods: Partial<Record<PeriodKey, RealEstateMapLayerPeriod>>) =>
  periods.week ?? periods.month ?? periods.quarter ?? periods.halfYear ?? periods.year ?? Object.values(periods)[0] ?? null;
const mapFeatureChangeLabel = (target: MapTarget) => {
  const period = usableMapPeriod(targetPeriodMeta(target));
  return period ? formatChange(period.changePct) : '자료 없음';
};
const subregionChangeLabel = (feature: SubregionFeature) => {
  const period = effectiveSubregionPeriod(feature);
  return period ? formatChange(period.changePct) : '공식 지수 미공표';
};
const subregionHeatColor = (feature: SubregionFeature) => {
  const period = effectiveSubregionPeriod(feature);
  return period ? mapHeatColor(period.changePct, subregionHeatScale.value) : unpublishedHeatColor;
};
const subregionGlowColor = (feature: SubregionFeature) =>
  hasSubregionPeriod(feature) ? subregionHeatColor(feature) : unpublishedGlowColor;
const nationalRepresentativePeriod = computed(() => {
  for (const target of targets) {
    const period = usableMapPeriod(targetPeriodMeta(target));
    if (period) return period;
  }

  return null;
});
const subregionRepresentativePeriod = computed(() => {
  for (const layerTarget of subregionLayerByCode.value.values()) {
    const period = usableMapPeriod(layerTarget.periods?.[activePeriod.value]);
    if (period) return period;
  }

  return null;
});
const mapUpdateBadgeLabel = computed(() => {
  const asOf = selectedRegion.value
    ? subregionRepresentativePeriod.value?.asOf
    : nationalRepresentativePeriod.value?.asOf;
  return `UPDATE: ${formatMapUpdateDate(asOf ?? mapLayerMeta.asOf)}`;
});
const applyTargetLayer = (target: MapTarget, layerTarget: RealEstateMapLayerTarget) => {
  target.targetId = layerTarget.targetId;
  target.geometryId = layerTarget.geometryId ?? target.geometryId;
  target.layerPeriods = layerTarget.periods;

  for (const period of periodOptions) {
    const periodValue = layerTarget.periods[period.id];
    if (periodValue) {
      target.periodChanges[period.id] = periodValue.changePct;
    }
  }

  const representative = firstPeriod(layerTarget.periods);
  if (representative) {
    target.sampleCount = representative.sampleCount;
    target.confidence = representative.confidence;
    target.asOf = representative.asOf;
    target.provider = representative.provider;
    target.sourceLabel = representative.sourceLabel;
    target.dataStatus = representative.dataStatus;
    target.stale = Boolean(representative.stale);
  }
};
const applyNationalMapLayer = (layer: RealEstateMapLayerResponse) => {
  if (!layer.targets.length) {
    mapLayerLoadState.value = 'fallback';
    return;
  }

  mapLayerMeta.asOf = layer.asOf ?? mapFixture.asOf;
  mapLayerMeta.dataStatus = layer.dataStatus ?? 'unknown';
  mapLayerMeta.mapDataSource = layer.mapDataSource ?? mapFixture.mapDataSource;
  mapLayerMeta.sourceLabel = layer.sourceLabel ?? mapFixture.sourceLabel;
  mapLayerMeta.stale = Boolean(layer.stale);

  for (const layerTarget of layer.targets) {
    const target = targetByRegionCode.get(layerTarget.regionCode);
    if (target) {
      applyTargetLayer(target, layerTarget);
    }
  }

  mapLayerLoadState.value = 'live';
};
const refreshNationalMapLayer = async () => {
  mapLayerLoadState.value = 'loading';
  try {
    applyNationalMapLayer(await fetchRealEstateMapLayer({ layerType: 'sido' }));
  } catch {
    mapLayerLoadState.value = 'fallback';
  }
};
const normalizeGeometryCode = (value?: string | null) => {
  const trimmed = value?.trim();
  if (!trimmed) return null;

  return trimmed.match(/\d{5}$/)?.[0] ?? trimmed;
};
const subregionLayerFeatureCodes = (target: RealEstateMapLayerTarget) =>
  Array.from(new Set([normalizeGeometryCode(target.geometryId), normalizeGeometryCode(target.regionCode)].filter(Boolean) as string[]));
const buildSubregionLayerIndex = (targets: RealEstateMapLayerTarget[]) => {
  const index = new Map<string, RealEstateMapLayerTarget>();

  for (const target of targets) {
    for (const code of subregionLayerFeatureCodes(target)) {
      index.set(code, target);
    }
  }

  return index;
};
const refreshSubregionMapLayer = async (region: MapTarget | null) => {
  if (!region) {
    subregionLayerByCode.value = new Map();
    subregionLayerLoadState.value = 'idle';
    return;
  }

  subregionLayerLoadState.value = 'loading';
  try {
    const layer = await fetchRealEstateMapLayer({ layerType: 'sigungu', parentTargetId: region.targetId });
    subregionLayerByCode.value = buildSubregionLayerIndex(layer.targets);
    subregionLayerLoadState.value = layer.targets.length ? 'live' : 'fallback';
  } catch {
    subregionLayerByCode.value = new Map();
    subregionLayerLoadState.value = 'fallback';
  }
};
const refreshMapEvidenceLogs = async (targetId: string | null) => {
  mapEvidenceLogs.value = [];
  if (!targetId) {
    mapEvidenceLoadState.value = 'idle';
    return;
  }

  mapEvidenceLoadState.value = 'loading';
  try {
    const logs = await fetchRealEstateTargetEvidenceLogs(targetId, { limit: 1 });
    mapEvidenceLogs.value = logs;
    mapEvidenceLoadState.value = logs.length ? 'live' : 'empty';
  } catch {
    mapEvidenceLogs.value = [];
    mapEvidenceLoadState.value = 'error';
  }
};
const refreshRegionalReport = async (targetId: string | null) => {
  regionalReport.value = null;
  if (!targetId) {
    regionalReportLoadState.value = 'idle';
    return;
  }

  regionalReportLoadState.value = 'loading';
  try {
    const report = await fetchRealEstateRegionalReport(targetId);
    regionalReport.value = report;
    regionalReportLoadState.value = report ? 'live' : 'empty';
  } catch {
    regionalReport.value = null;
    regionalReportLoadState.value = 'error';
  }
};
const mapLayerStatusText = computed(() => {
  if (mapLayerLoadState.value === 'loading') return `loading · ${mapFixture.asOf}`;
  if (mapLayerLoadState.value === 'fallback') return `mock fallback · ${mapFixture.asOf}`;
  const freshness = mapLayerMeta.stale ? 'stale' : 'fresh';
  return `${mapLayerMeta.dataStatus ?? 'unknown'} · ${freshness} · ${mapLayerMeta.asOf ?? 'asOf unknown'}`;
});
const mapDataSourceLabel = computed(() => mapLayerMeta.mapDataSource ?? mapFixture.mapDataSource);
const dokdoSeodo = computed(() => { const p = nationalProjection([131.8624, 37.2433]); return p ? { x: p[0], y: p[1] } : null; });
const dokdoDongdo = computed(() => { const p = nationalProjection([131.8684, 37.2417]); return p ? { x: p[0], y: p[1] } : null; });
const subregionLayerStatusText = computed(() => {
  if (!selectedRegion.value) return '전국';
  if (subregionLayerLoadState.value === 'loading') return '하위 레이어 로딩';
  return '하위지역 기준';
});

const selectedEvidenceLayerTarget = computed(() =>
  selectedSubregion.value ? subregionLayerTargetForFeature(selectedSubregion.value) : null
);
const selectedReportUsesParentTarget = computed(() =>
  Boolean(
    selectedRegion.value
    && selectedSubregion.value
    && parentOnlyReportTargetIds.has(selectedRegion.value.targetId)
  )
);
const selectedEvidenceTargetId = computed(() =>
  selectedReportUsesParentTarget.value
    ? selectedRegion.value?.targetId ?? null
    : selectedEvidenceLayerTarget.value?.targetId ?? selectedRegion.value?.targetId ?? null
);
const latestMapEvidenceLog = computed(() => mapEvidenceLogs.value[0] ?? null);
const latestRegionalReport = computed(() =>
  regionalReport.value?.targetId === selectedEvidenceTargetId.value ? regionalReport.value : null
);
const mapEvidenceStatusText = computed(() => {
  if (!selectedRegion.value) return '지역 선택 전';
  if (mapEvidenceLoadState.value === 'loading') return 'AI 근거 로그 확인 중';
  if (mapEvidenceLoadState.value === 'live') return 'AI 근거 반영';
  if (mapEvidenceLoadState.value === 'empty') return 'AI 근거 로그 수집 전/insufficient';
  if (mapEvidenceLoadState.value === 'error') return 'AI 근거 확인 필요';
  return 'AI 근거 로그 대기';
});
const visibleMapEvidenceItems = computed<RealEstateEvidenceItem[]>(() =>
  (latestMapEvidenceLog.value?.evidenceItems ?? [])
    .filter((item) => item.evidenceItemId && item.label)
    .slice(0, 5)
);
const selectedReport = computed(() => {
  if (!selectedRegion.value) return null;

  const feature = selectedSubregion.value;
  const target = selectedRegion.value;
  const usesParentTarget = selectedReportUsesParentTarget.value;
  const subjectName = usesParentTarget ? target.name : feature?.name ?? target.name;
  const subjectCode = usesParentTarget ? target.regionCode : feature?.code ?? target.regionCode;
  const change = feature ? subregionPeriodChange(feature) : periodChange(target);
  const sampleCount = feature ? subregionSampleCount(feature) : targetSampleCount(target);
  const confidence = feature ? subregionConfidence(feature) : targetConfidence(target);
  const confidencePct = confidencePercent(confidence);
  const directSubregionPeriod = feature ? usableMapPeriod(subregionLayerPeriod(feature)) : null;
  const livePeriod = feature ? effectiveSubregionPeriod(feature) : usableMapPeriod(targetPeriodMeta(target));
  const reportBasePeriod = usesParentTarget || !feature
    ? usableMapPeriod(targetPeriodMeta(target, 'month'))
      ?? usableMapPeriod(targetPeriodMeta(target, 'quarter'))
      ?? usableMapPeriod(targetPeriodMeta(target, 'halfYear'))
      ?? usableMapPeriod(targetPeriodMeta(target, 'year'))
      ?? usableMapPeriod(targetPeriodMeta(target, 'week'))
    : usableMapPeriod(subregionLayerPeriod(feature, 'month'))
      ?? usableMapPeriod(subregionLayerPeriod(feature, 'quarter'))
      ?? usableMapPeriod(subregionLayerPeriod(feature, 'halfYear'))
      ?? usableMapPeriod(subregionLayerPeriod(feature, 'year'))
      ?? usableMapPeriod(subregionLayerPeriod(feature, 'week'));
  const hasLivePeriod = Boolean(livePeriod);
  const storedReport = latestRegionalReport.value;
  const storedReportParagraphs = reportBodyParagraphs(storedReport?.body);
  const isDerivedSubregionPeriod = Boolean(feature && livePeriod && !directSubregionPeriod);
  const sourceLabel = livePeriod ? mapSourceLabel(livePeriod.provider ?? livePeriod.sourceLabel) : '출처 확인 필요';
  const dataStatusLabel = mapDataStatusLabel(livePeriod?.dataStatus) ?? '확인 필요';
  const asOfLabel = formatMapTimestamp(livePeriod?.asOf);
  const reportUpdatedAtLabel = formatMapTimestamp(storedReport?.publishedAt ?? latestMapEvidenceLog.value?.asOf ?? reportBasePeriod?.asOf ?? livePeriod?.asOf);
  const freshnessLabel = livePeriod
    ? isDerivedSubregionPeriod
      ? '상위 지역만 반영'
      : livePeriod.stale
        ? '공개 지연 가능'
        : '최신 반영'
    : '수집 전';
  const layerStatus = livePeriod
    ? `${sourceLabel} · ${dataStatusLabel} · ${freshnessLabel}`
    : '시장 사실 수집 전';
  const mentionCount = hasLivePeriod ? Math.round(sampleCount * (1.18 + Math.abs(change) * 0.72)) : 0;
  const previousMentionCount = hasLivePeriod ? Math.max(1, Math.round(mentionCount / (1.16 + Math.abs(change) * 0.28))) : 0;
  const mentionDeltaPct = hasLivePeriod && previousMentionCount > 0
    ? Math.round(((mentionCount - previousMentionCount) / previousMentionCount) * 100)
    : 0;
  const evidenceLabels = visibleMapEvidenceItems.value
    .filter((item) => item.evidenceType !== 'market_fact')
    .map(mapEvidenceIssueLabel)
    .slice(0, 3);
  const reportIssues = evidenceLabels.length
    ? evidenceLabels
    : hasLivePeriod
      ? target.issues
      : ['시장 사실 수집 전', '분석 근거 확인 필요'];
  const primaryIssue = reportIssues[0] ?? '지역 반응';
  const secondaryIssue = reportIssues[1] ?? '시장 사실';
  const unavailableValue = '수집 전';
  const priceValue = hasLivePeriod ? `${periodLabelById[activePeriod.value]} ${formatChange(change)}` : '공식 데이터 없음';
  const reportEvidenceState = latestMapEvidenceLog.value
    ? '분석 근거 반영'
    : mapEvidenceLoadState.value === 'loading'
      ? '분석 근거 확인 중'
      : mapEvidenceLoadState.value === 'error'
        ? '분석 근거 확인 필요'
        : '분석 근거 수집 전';
  const latestReportEvidenceState = storedReport
    ? '최신 리포트 DB 반영'
    : regionalReportLoadState.value === 'loading'
      ? '최신 리포트 확인 중'
      : regionalReportLoadState.value === 'error'
        ? '최신 리포트 확인 필요'
        : reportEvidenceState;
  const evidenceValue = latestMapEvidenceLog.value ? '분석 근거 확인' : unavailableValue;
  const changeDirectionLabel = hasLivePeriod
    ? change > 0.05
      ? '상승 흐름'
      : change < -0.05
        ? '하락 흐름'
        : '보합권'
    : '공식 가격지수 수집 전';
  const selectedPeriodLabel = periodLabelById[activePeriod.value];
  const directDataScope = usesParentTarget
    ? '상위 리포트 기준으로 통합'
    : isDerivedSubregionPeriod
      ? '상위 지역만 반영'
      : feature
        ? '하위 지역 직접 지표 우선'
        : '지역 전체 공식 지표 우선';
  const fallbackExpectationPoints = [
    livePeriod ? '공식 가격지수 확인' : '공식 가격지수 수집 전',
    latestReportEvidenceState,
    directDataScope
  ];
  const expectationPoints = storedReport?.expectationPoints.length
    ? storedReport.expectationPoints
    : fallbackExpectationPoints;
  const fallbackConcernPoints = [
    hasLivePeriod && change < 0
      ? `${selectedPeriodLabel} 가격지수 ${formatChange(change)} 하락`
      : '선택 기간 수치만으로 흐름 단정 금지',
    '매매 실거래 연결 전',
    '전월세·공급 일정 연결 전'
  ];
  const concernPoints = storedReport?.concernPoints.length
    ? storedReport.concernPoints
    : fallbackConcernPoints;
  const analysisParagraphs = storedReportParagraphs.length
    ? storedReportParagraphs
    : hasLivePeriod
    ? [
        `${subjectName} 리포트는 ${reportUpdatedAtLabel} 업데이트 기준으로 정리했습니다. 첫 수치 박스는 현재 지도에서 선택한 ${selectedPeriodLabel} 가격지수 변화 ${formatChange(change)}를 보여주는 렌즈입니다.`,
        `판단은 ${sourceLabel} 가격지수와 연결된 분석 근거를 우선 보고, 매매 실거래·전월세·공급 일정은 연결 전 항목으로 분리해 해석합니다.`,
        `기간별 등락률은 지도 색을 읽기 위한 보조 수치입니다. 리포트 본문은 기간 탭마다 새로 쓰지 않고 최신 기준의 기대 지점과 우려 지점을 하나로 유지합니다.`
      ]
    : [
        `${subjectName} 리포트는 ${reportUpdatedAtLabel} 업데이트 기준입니다. 공식 가격지수가 아직 화면에 연결되지 않아 값을 임의 추정하지 않습니다.`,
        `분석 근거와 공식 시장 사실이 연결되면 최신 기준의 지역 브리핑으로 전환합니다.`,
        '매매 실거래, 전월세, 공급 일정은 각각 별도 근거로 확인한 뒤 같은 리포트에 적재합니다.'
      ];
  const analysisSegments = reportAnalysisSegments(analysisParagraphs);
  const relatedReports = storedReport?.sources.length
    ? storedReport.sources.map((source) => ({
        label: source.label,
        title: source.title,
        meta: regionalReportSourceMeta(source),
        url: source.url ?? null
      }))
    : [
        {
          label: '가격지수',
          title: livePeriod ? `${sourceLabel} 가격지수` : '한국부동산원 가격지수',
          meta: livePeriod ? `${reportUpdatedAtLabel} 업데이트` : '공식 데이터 없음',
          url: null
        },
        {
          label: '실거래',
          title: '매매 실거래 공개시스템',
          meta: '수집 전',
          url: null
        },
        {
          label: '뉴스·리포트',
          title: `${subjectName} 관련 뉴스·리포트`,
          meta: latestMapEvidenceLog.value ? '분석 근거 반영 · 원문 링크 적재 대기' : '수집 전',
          url: null
        }
      ];

  return {
    change,
    confidence: confidencePct,
    dataStatusLabel,
    asOfLabel,
    reportUpdatedAtLabel,
    freshnessLabel,
    hasLivePeriod,
    mentionCount,
    mentionDeltaPct,
    previousMentionCount,
    issues: reportIssues,
    metrics: [
      { label: '가격 흐름', value: priceValue, meta: '한국부동산원 가격지수' },
      { label: '실거래', value: unavailableValue, meta: '국토교통부 매매 실거래 연결 전' },
      { label: '전세 압력', value: evidenceValue, meta: '전월세 실거래와 근거 로그 기준' },
      { label: '공급·정책', value: evidenceValue, meta: '청약·미분양·정책 일정 기준' }
    ],
    name: feature && !usesParentTarget ? `${target.name} ${subjectName}` : `${target.name} 전체`,
    regionLevelLabel: feature && !usesParentTarget ? '시군구' : '시도 전체',
    sampleCount,
    sourceMix: [
      { label: '출처', value: livePeriod ? sourceLabel : unavailableValue },
      { label: '수집 상태', value: dataStatusLabel },
      { label: '기준 시각', value: asOfLabel },
      { label: '갱신 상태', value: freshnessLabel }
    ],
    officialFacts: [
      {
        label: '가격지수',
        value: hasLivePeriod ? formatChange(change) : '공식 데이터 없음',
        meta: livePeriod ? `${sourceLabel} · ${asOfLabel}` : '한국부동산원 지도 레이어 수집 전',
        status: dataStatusLabel
      },
      {
        label: '매매 실거래',
        value: unavailableValue,
        meta: '국토교통부 매매 실거래 연결 전',
        status: '수집 전'
      },
      {
        label: '전월세',
        value: unavailableValue,
        meta: '국토교통부 전월세 실거래 연결 전',
        status: '수집 전'
      },
      {
        label: '공개 지연',
        value: livePeriod?.stale ? '공개 지연 가능' : livePeriod ? '최신 반영' : '확인 필요',
        meta: '원천 기준 시각과 화면 반영 시각을 분리해서 표시',
        status: freshnessLabel
      }
    ],
    keyChanges: [
      {
        label: '가격 흐름',
        value: hasLivePeriod ? formatChange(change) : '공식 데이터 없음',
        meta: livePeriod ? `${periodLabelById[activePeriod.value]} · 가격지수 · ${sourceLabel}` : '한국부동산원 지도 레이어 수집 전'
      },
      {
        label: '거래 확인',
        value: unavailableValue,
        meta: '국토교통부 매매 실거래 연결 전'
      },
      {
        label: '전세·공급 압력',
        value: evidenceValue,
        meta: '전월세 실거래·청약·정책 일정 연결 후 보강'
      }
    ],
    reportCautions: [
      {
        label: '공개 기준',
        value: livePeriod ? `${asOfLabel} · ${freshnessLabel}` : '수집 전'
      },
      {
        label: '자료 범위',
        value: usesParentTarget
          ? '단일 행정계층 · 상위 리포트 기준'
          : isDerivedSubregionPeriod
            ? '상위 지역만 반영'
            : '직접 지표 우선 · 없으면 상위 지역만 반영'
      },
      {
        label: '분석 근거',
        value: latestReportEvidenceState
      }
    ],
    comparisonRows: feature && !usesParentTarget
      ? [
          {
            label: '상위 지역',
            value: `${target.name} 전체`,
            meta: usableMapPeriod(targetPeriodMeta(target)) ? formatChange(periodChange(target)) : '상위 지역 수집 전'
          },
          { label: '생활권·동 후보', value: unavailableValue, meta: 'target graph 연결 후 표시' },
          { label: '단지 후보', value: unavailableValue, meta: '좌표와 alias 검증 후 표시' }
        ]
      : [
          {
            label: '가장 강한 하위 지역',
            value: strongestSubregion.value?.name ?? '수집 전',
            meta: strongestSubregion.value ? formatChange(subregionPeriodChange(strongestSubregion.value)) : '하위 시군구 수집 전'
          },
          { label: '시군구 비교', value: `${subregionFeatures.value.length}개 구·시·군`, meta: '지도 레이어 기준' },
          { label: '생활권·단지 후보', value: unavailableValue, meta: '후속 target graph 연결 대상' }
        ],
    scheduleRows: [
      { label: '청약·공급', value: unavailableValue, meta: '주요 일정 데이터 연결 후 표시' },
      { label: '미분양·인허가', value: unavailableValue, meta: '공급 선행지표 연결 후 표시' },
      { label: '정책·교통', value: evidenceValue, meta: 'timeline 이벤트와 공식 일정 기준' }
    ],
    evidenceLimits: [
      { label: '출처', value: livePeriod ? sourceLabel : '수집 전' },
      { label: '기준 시각', value: asOfLabel },
      { label: '갱신 상태', value: freshnessLabel },
      { label: '하위 지역 보정', value: usesParentTarget ? '단일 행정계층 · 상위 리포트 기준' : isDerivedSubregionPeriod ? '상위 지역만 반영' : '직접 지표 우선 · 없으면 상위 지역만 반영' },
      { label: '분석 근거', value: latestReportEvidenceState }
    ],
    summary: storedReport?.summary ?? (hasLivePeriod
      ? `${subjectName}의 ${periodLabelById[activePeriod.value]} 가격지수 변화는 ${formatChange(change)}입니다. 현재 지도 레이어는 ${layerStatus} 상태이며, 실거래·전월세·공급 일정은 연결 전 항목을 분리해서 확인합니다.${isDerivedSubregionPeriod ? ' 아직 시군구 직접 지표가 없어 상위 지역만 반영한 상태입니다.' : ''}`
      : `${subjectName} 지도 흐름 자료는 아직 수집 전입니다. 이 구간은 값을 임의 추정하지 않고, 상위 지역 분석 근거와 하위 지역 갱신 배치가 연결되면 실제 리포트로 전환됩니다.`),
    expectationPoints,
    concernPoints,
    analysisParagraphs,
    analysisSegments,
    relatedReports,
    title: '보조 반응',
    mentionSummary: hasLivePeriod
      ? `${subjectName} 관련 공개 원문 반응은 공식 시장 사실을 해석하는 보조 관찰로만 표시합니다.`
      : `${subjectName} 보조 반응 자료는 아직 수집 전 상태입니다.`,
    bullets: hasLivePeriod
      ? [
          `공개 원문 언급은 ${previousMentionCount}건에서 ${mentionCount}건으로 관찰됐습니다.`,
          `${primaryIssue}와 ${secondaryIssue}는 가격 판단이 아니라 이슈 맥락을 보강하는 라벨입니다.`,
          `표본과 출처 기준의 관찰 요약이며, ${isDerivedSubregionPeriod ? '상위 지역만 반영한 상태입니다.' : '출처와 기준 시각을 함께 확인해야 합니다.'}`
        ]
      : [
          `${subjectName} 지도 흐름과 보조 반응 자료는 아직 충분하지 않습니다.`,
          `${target.name} 상위 지역 분석 근거가 있으면 우선 표시하고, 하위 구간 값은 임의로 채우지 않습니다.`,
          '공식 데이터, 근거 링크, 보조 반응이 연결되면 이 패널은 실제 수치 리포트로 전환됩니다.'
        ],
    previewComplexes: [],
    subregionCode: subjectCode,
    subregionName: subjectName
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

const selectedRegionRecentView = computed(() => {
  const region = selectedRegion.value;
  if (!region) return null;

  const subregion = selectedSubregion.value;
  if (!subregion) {
    return {
      id: region.targetId,
      kind: 'region' as const,
      label: region.name,
      meta: `지역 분석 · ${periodLabelById[activePeriod.value]}`,
      href: `/realestate/map/${region.targetId}`
    };
  }

  const params = new URLSearchParams();
  const selectedTargetId = selectedEvidenceLayerTarget.value?.targetId ?? selectedEvidenceTargetId.value;
  if (selectedTargetId) {
    params.set('selectedTargetId', selectedTargetId);
  }
  params.set('selectedRegionCode', subregion.code);
  params.set('period', activePeriod.value);

  return {
    id: selectedTargetId ?? `${region.targetId}-${subregion.code}`,
    kind: 'region' as const,
    label: selectedReport.value?.name ?? `${region.name} ${subregion.name}`,
    meta: `지역 분석 · ${region.name} · ${periodLabelById[activePeriod.value]}`,
    href: `/realestate/map/${region.targetId}?${params.toString()}`
  };
});
const selectedRegionWatchTarget = computed<UserWatchTargetPayload | null>(() => {
  const view = selectedRegionRecentView.value;
  if (!view) return null;

  return {
    targetType: 'region',
    targetId: view.id,
    displayName: view.label,
    landingPath: view.href
  };
});
const isSelectedRegionWatched = computed(() => {
  const target = selectedRegionWatchTarget.value;
  return target ? isUserWatchTargetSaved(target.targetType, target.targetId) : false;
});
const selectedRegionWatchTestId = computed(() => {
  const target = selectedRegionWatchTarget.value;
  return target ? `watch-toggle-region-${safeWatchTargetTestId(target.targetId)}` : 'watch-toggle-region';
});
const selectedRegionWatchLabel = computed(() => {
  const target = selectedRegionWatchTarget.value;
  if (!target) return '관심 저장';
  return isSelectedRegionWatched.value ? `${target.displayName} 관심 해제` : `${target.displayName} 관심 저장`;
});
const selectedRegionChatAttachment = computed<ChatAttachmentPayload | null>(() => {
  const target = selectedRegionWatchTarget.value;
  const report = selectedReport.value;
  if (!target || !report) return null;

  return {
    type: 'region',
    targetId: target.targetId,
    title: target.displayName,
    subtitle: `지역 분석 · ${periodLabelById[activePeriod.value]}`,
    metricLabel: periodLabelById[activePeriod.value],
    metricValue: report.hasLivePeriod ? formatChange(report.change) : '자료 없음',
    metricTone: report.hasLivePeriod ? changeTone(report.change) : 'flat',
    landingPath: target.landingPath
  };
});
const selectedRegionChatTestId = computed(() => {
  const target = selectedRegionChatAttachment.value;
  return target ? `chat-attach-region-${safeWatchTargetTestId(target.targetId)}` : 'chat-attach-region';
});
const selectedRegionChatLabel = computed(() => {
  const target = selectedRegionChatAttachment.value;
  return target ? `${target.title} 채팅에 첨부` : '지역 리포트 채팅에 첨부';
});

const dispatchChatAttachment = (attachment: ChatAttachmentPayload) => {
  window.dispatchEvent(new CustomEvent('ybf-chat-attach', { detail: attachment }));
};

const attachSelectedRegionToChat = () => {
  const attachment = selectedRegionChatAttachment.value;
  if (!attachment) return;
  dispatchChatAttachment(attachment);
};

const toggleSelectedRegionWatch = async () => {
  const target = selectedRegionWatchTarget.value;
  if (!target) return;

  if (!currentAuthUser.value) {
    await router.push('/auth/login');
    return;
  }

  if (isSelectedRegionWatched.value) {
    await removeUserWatchTarget(target.targetType, target.targetId);
  } else {
    await saveUserWatchTarget(target);
  }
};

watch(
  selectedRegionRecentView,
  (view) => {
    if (view) {
      recordRecentRealEstateView(view);
    }
  },
  { immediate: true }
);

const clampMapPan = (scale: number, panX: number, panY: number, shell?: HTMLElement) => {
  if (scale <= minMapZoom + 0.01) {
    return { panX: 0, panY: 0 };
  }

  const width = shell?.clientWidth ?? 980;
  const height = shell?.clientHeight ?? 760;
  const maxPanX = Math.max(0, width * (scale - 1) * 0.42);
  const maxPanY = Math.max(0, height * (scale - 1) * 0.42);

  return {
    panX: Math.min(maxPanX, Math.max(-maxPanX, panX)),
    panY: Math.min(maxPanY, Math.max(-maxPanY, panY))
  };
};
const updateMapViewport = (scale: number, panX: number, panY: number, shell?: HTMLElement) => {
  const nextScale = Math.min(maxMapZoom, Math.max(minMapZoom, scale));
  const nextPan = clampMapPan(nextScale, panX, panY, shell);

  mapViewport.scale = nextScale;
  mapViewport.panX = nextPan.panX;
  mapViewport.panY = nextPan.panY;
};
const resetMapViewport = () => {
  mapViewport.scale = minMapZoom;
  mapViewport.panX = 0;
  mapViewport.panY = 0;
  mapViewport.isDragging = false;
  mapViewport.dragMoved = false;
  mapViewport.suppressClick = false;
};
const isMapControlTarget = (target: EventTarget | null) =>
  target instanceof Element && Boolean(target.closest('a, button, .map-zoom-controls'));
const handleMapWheel = (event: WheelEvent) => {
  const shell = event.currentTarget as HTMLElement;
  const previousScale = mapViewport.scale;
  const zoomFactor = Math.exp(-event.deltaY * 0.0016);
  const nextScale = Math.min(maxMapZoom, Math.max(minMapZoom, previousScale * zoomFactor));
  const rect = shell.getBoundingClientRect();
  const focusX = event.clientX - rect.left - rect.width / 2;
  const focusY = event.clientY - rect.top - rect.height / 2;
  const scaleRatio = nextScale / previousScale;
  const nextPanX = mapViewport.panX + (focusX - mapViewport.panX) * (1 - scaleRatio);
  const nextPanY = mapViewport.panY + (focusY - mapViewport.panY) * (1 - scaleRatio);

  updateMapViewport(nextScale, nextPanX, nextPanY, shell);
};
const adjustMapZoom = (direction: 'in' | 'out') => {
  const delta = direction === 'in' ? 0.35 : -0.35;
  updateMapViewport(mapViewport.scale + delta, mapViewport.panX, mapViewport.panY);
};
const focusSubregionCluster = (cluster: SubregionCluster) => {
  selectedSubregionClusterId.value = cluster.id;
  selectedSubregionCode.value = null;
  resetMapViewport();
};
const clearSubregionClusterFocus = () => {
  selectedSubregionClusterId.value = null;
  selectedSubregionCode.value = null;
  resetMapViewport();
};
const handleMapPointerDown = (event: PointerEvent) => {
  if (event.button !== 0 || mapViewport.scale <= minMapZoom + 0.01 || isMapControlTarget(event.target)) {
    return;
  }

  mapViewport.isDragging = true;
  mapViewport.dragMoved = false;
  mapViewport.lastX = event.clientX;
  mapViewport.lastY = event.clientY;
  (event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId);
  event.preventDefault();
};
const handleMapPointerMove = (event: PointerEvent) => {
  if (!mapViewport.isDragging) return;

  const deltaX = event.clientX - mapViewport.lastX;
  const deltaY = event.clientY - mapViewport.lastY;
  if (Math.abs(deltaX) > 1 || Math.abs(deltaY) > 1) {
    mapViewport.dragMoved = true;
  }

  mapViewport.lastX = event.clientX;
  mapViewport.lastY = event.clientY;
  updateMapViewport(mapViewport.scale, mapViewport.panX + deltaX, mapViewport.panY + deltaY, event.currentTarget as HTMLElement);
};
const stopMapPointerDrag = (event: PointerEvent) => {
  if (!mapViewport.isDragging) return;

  if (mapViewport.dragMoved) {
    mapViewport.suppressClick = true;
    window.setTimeout(() => {
      mapViewport.suppressClick = false;
    }, 120);
  }

  mapViewport.isDragging = false;
  (event.currentTarget as HTMLElement).releasePointerCapture?.(event.pointerId);
};
const handleMapClickCapture = (event: MouseEvent) => {
  if (!mapViewport.suppressClick) return;

  event.preventDefault();
  event.stopPropagation();
};

function mapEvidenceIssueLabel(item: RealEstateEvidenceItem): string {
  if (item.evidenceType === 'reaction') return '커뮤니티 반응';
  if (item.evidenceType === 'search_candidate') return '최근 이슈 후보';
  if (item.evidenceType === 'timeline_event') return '타임라인 이벤트';
  if (item.evidenceType === 'similar_window') return '유사 과거 사례';
  return item.label;
}

function reportBodyParagraphs(body?: string | null): string[] {
  return (body ?? '')
    .split(/\n+/)
    .map((paragraph) => paragraph.trim())
    .filter((paragraph) => paragraph.length > 0);
}

function reportAnalysisSegments(paragraphs: string[]): ReportAnalysisSegment[] {
  const segments = paragraphs.flatMap((paragraph, paragraphIndex) => {
    const normalized = paragraph.replace(/\s+/g, ' ').trim();
    if (!normalized) return [];

    const matches = Array.from(normalized.matchAll(/(평가|전망)\s*:/g));
    if (!matches.length) {
      return [{
        key: `paragraph-${paragraphIndex}`,
        label: null,
        text: normalized
      }];
    }

    const parsed = matches
      .map((match, matchIndex) => {
        const start = (match.index ?? 0) + match[0].length;
        const nextStart = matches[matchIndex + 1]?.index ?? normalized.length;
        return {
          key: `${match[1]}-${paragraphIndex}-${matchIndex}`,
          label: match[1] as '평가' | '전망',
          text: normalized.slice(start, nextStart).trim()
        };
      })
      .filter((segment) => segment.text.length > 0);

    const leadingText = normalized.slice(0, matches[0]?.index ?? 0).trim();
    return leadingText
      ? [{ key: `lead-${paragraphIndex}`, label: null, text: leadingText }, ...parsed]
      : parsed;
  });

  return segments.length ? segments : [{ key: 'empty', label: null, text: '분석 리포트 본문 수집 전입니다.' }];
}

function regionalReportSourceMeta(source: RealEstateRegionalReport['sources'][number]): string {
  return [
    source.sourceName,
    source.dataStatus,
    formatMapTimestamp(source.publishedAt)
  ].filter((value): value is string => Boolean(value && value !== '기준 시각 확인 필요')).join(' · ') || '근거 확인 필요';
}

const navigateToRegion = (target: MapTarget) => {
  void router.push(`/realestate/map/${target.targetId}`);
};
const selectSubregion = (code: string) => {
  const feature = subregionFeatures.value.find((candidate) => candidate.code === code);
  if (!feature || isSubregionUnavailable(feature)) {
    return;
  }

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
const selectSubregionFromMap = (code: string) => {
  if (showSubregionClusters.value) return;
  selectSubregion(code);
};
const selectableSubregionCode = (code?: string | null) => {
  const normalized = normalizeGeometryCode(code);
  if (!normalized) return null;

  const feature = subregionFeatures.value.find((candidate) => candidate.code === normalized);
  if (!feature || isSubregionUnavailable(feature)) return null;

  return normalized;
};
const selectedRouteSubregionCode = () => {
  const selectedTargetId = routeSelectedTargetId.value;
  if (selectedTargetId) {
    const layerTarget = Array.from(new Set(subregionLayerByCode.value.values()))
      .find((target) => target.targetId === selectedTargetId);
    if (layerTarget) {
      for (const code of subregionLayerFeatureCodes(layerTarget)) {
        const selectableCode = selectableSubregionCode(code);
        if (selectableCode) return selectableCode;
      }
    }
  }

  return selectableSubregionCode(routeSelectedRegionCode.value);
};
const syncSelectedSubregionFromRoute = () => {
  if (!selectedRegion.value) return;

  const code = selectedRouteSubregionCode();
  if (!code || selectedSubregionCode.value === code) return;

  selectSubregion(code);
};
const resetReportState = () => {
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
const closeReport = () => {
  if (selectedRegion.value && !selectedSubregionCode.value) {
    void router.push('/realestate/map');
    return;
  }

  resetReportState();
};

watch(
  () => route.params.regionId,
  () => {
    selectedSubregionClusterId.value = null;
    resetReportState();
    resetMapViewport();
  }
);
watch(
  routeSelectedPeriod,
  (period) => {
    if (period && activePeriod.value !== period) {
      activePeriod.value = period;
    }
  },
  { immediate: true }
);
watch(
  [routeSelectedTargetId, routeSelectedRegionCode, selectedRegion, subregionFeatures, subregionLayerByCode],
  syncSelectedSubregionFromRoute,
  { immediate: true }
);
watch(
  selectedRegion,
  (region) => {
    if (region) {
      void loadMunicipalityTopology();
    }
    void refreshSubregionMapLayer(region);
  },
  { immediate: true }
);
watch(
  selectedEvidenceTargetId,
  (targetId) => {
    void refreshMapEvidenceLogs(targetId);
    void refreshRegionalReport(targetId);
  },
  { immediate: true }
);
onMounted(() => {
  if (currentAuthUser.value) {
    void loadUserWatchTargets();
  }
  void refreshNationalMapLayer();
  batchUpdateSubscription = subscribeRealEstateBatchUpdates((event) => {
    if (event.topic !== 'map-layers') {
      return;
    }
    void refreshNationalMapLayer();
    if (selectedRegion.value) {
      void refreshSubregionMapLayer(selectedRegion.value);
    }
  });
});
onBeforeUnmount(() => {
  batchUpdateSubscription?.close();
  batchUpdateSubscription = null;
});
</script>

<template>
  <section
    :class="[
      'realestate-map-page',
      {
        'has-report': selectedReport,
        'is-drilldown': selectedRegion,
        'is-incheon-drilldown': selectedRegion?.regionCode === '23'
      }
    ]"
    aria-labelledby="realestate-map-title"
  >
    <header class="map-page-header">
      <div>
        <h2 id="realestate-map-title">{{ pageTitle }}</h2>
        <p>{{ pageDescription }}</p>
      </div>
      <div v-if="selectedRegion" class="map-header-actions">
        <RouterLink
          v-if="hasTransactionData"
          class="transaction-map-cta"
          :to="transactionMapLink"
          data-testid="region-transaction-map-link"
        >
          🗺️ {{ transactionMapLabel }}
        </RouterLink>
        <span
          v-else
          class="transaction-map-cta is-empty"
          data-testid="region-transaction-map-empty"
          aria-disabled="true"
        >
          {{ transactionMapLabel }}
        </span>
      </div>
    </header>

    <section
      :class="['realestate-map-layout', layoutMode]"
      data-testid="realestate-map-layout"
      aria-label="지도와 선택 리포트"
    >
      <article class="realestate-map-stage" aria-labelledby="korea-map-title">
        <div class="map-stage-toolbar">
          <div class="map-stage-heading-line">
            <div class="map-stage-title-stack">
              <p class="label">{{ selectedRegion ? '지역 상세 지도' : '전국 흐름 지도' }}</p>
              <h3 id="korea-map-title">
                {{
                  focusedSubregionClusterLabel
                    ? `${focusedSubregionClusterLabel} 상세 흐름`
                    : selectedRegion
                      ? `${selectedRegion.name} 상세 흐름`
                      : '전국 부동산 흐름'
                }}
              </h3>
            </div>
            <div class="map-period-control" aria-label="지도 기간 선택">
              <div class="map-period-tabs map-period-slider" role="radiogroup" :style="periodSliderStyle">
                <span class="map-period-slider-thumb" aria-hidden="true"></span>
                <button
                  v-for="period in periodOptions"
                  :key="period.id"
                  type="button"
                  role="radio"
                  :aria-checked="activePeriod === period.id"
                  :class="['map-period-option', { active: activePeriod === period.id }]"
                  @click="activePeriod = period.id"
                >
                  <span class="map-period-option-label">{{ period.label }}</span>
                </button>
              </div>
            </div>
          </div>
          <div class="map-toolbar-right">
            <span class="map-update-badge" data-testid="map-update-badge">{{ mapUpdateBadgeLabel }}</span>
            <div class="map-legend" aria-label="지역 색상 범례">
              <span><i class="up"></i>상승</span>
              <span><i class="down"></i>하락</span>
              <span><i class="empty"></i>공식 지수 미공표</span>
            </div>
          </div>
        </div>

        <div
          :class="['korea-map-shell', { 'is-map-panning': mapViewport.isDragging, 'is-map-zoomed': isMapZoomed }]"
          data-testid="korea-map-shell"
          @wheel.prevent="handleMapWheel"
          @pointerdown="handleMapPointerDown"
          @pointermove="handleMapPointerMove"
          @pointerup="stopMapPointerDrag"
          @pointercancel="stopMapPointerDrag"
          @click.capture="handleMapClickCapture"
        >
          <RouterLink
            v-if="selectedRegion"
            class="map-return-cta map-surface-return"
            to="/realestate/map"
            aria-label="전국 지도로 돌아가기"
          >
            <span>←</span>
            <strong>전국 지도로 돌아가기</strong>
          </RouterLink>
          <button
            v-if="focusedSubregionClusterLabel"
            class="map-return-cta map-cluster-return"
            type="button"
            data-testid="subregion-focus-return"
            :aria-label="`${selectedRegion?.name} 전체 권역 보기`"
            @click="clearSubregionClusterFocus"
          >
            <span>←</span>
            <strong>{{ selectedRegion?.name }} 전체 권역 보기</strong>
          </button>
          <div
            :class="['korea-map-board', { 'region-drilldown-map-board': selectedRegion }]"
            :style="mapBoardStyle"
            data-testid="korea-map-board"
          >
            <div class="map-surface-layer">
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
                    :transform="feature.depthTransform"
                  />
                </g>
                <g class="region-glow-layer" aria-hidden="true">
                  <path
                    v-for="feature in mapFeatures"
                    :key="`${feature.code}-glow`"
                    :d="feature.path"
                    :transform="feature.pathTransform"
                    :class="['region-glow', changeTone(periodChange(feature.target))]"
                    :style="{ stroke: nationalRegionHeatColor(feature.target) }"
                  />
                </g>
                <g>
                  <path
                    v-for="feature in mapFeatures"
                    :key="feature.target.id"
                    :d="feature.path"
                    :class="['region-shape', changeTone(periodChange(feature.target))]"
                    :style="{ fill: nationalRegionHeatColor(feature.target) }"
                    :transform="feature.pathTransform"
                    :aria-label="`${feature.target.name} ${mapFeatureChangeLabel(feature.target)}`"
                    @click="navigateToRegion(feature.target)"
                    @mouseenter="hoveredRegionCode = feature.code"
                    @mouseleave="hoveredRegionCode = null"
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
                <g v-if="dokdoSeodo && dokdoDongdo" :class="['dokdo-marker', { glow: hoveredRegionCode === '37' }]" aria-label="독도">
                  <ellipse class="dokdo-dot seodo" :cx="dokdoSeodo.x" :cy="dokdoSeodo.y" rx="2.2" ry="3.4" :transform="`rotate(-20 ${dokdoSeodo.x} ${dokdoSeodo.y})`" />
                  <ellipse class="dokdo-dot dongdo" :cx="dokdoDongdo.x" :cy="dokdoDongdo.y" rx="1.8" ry="2.4" :transform="`rotate(10 ${dokdoDongdo.x} ${dokdoDongdo.y})`" />
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
                  <path
                    v-for="feature in subregionFeatures"
                    :key="`${feature.code}-depth`"
                    :d="feature.path"
                    :transform="detailExtrusionTransform"
                  />
                </g>
                <g class="region-glow-layer" aria-hidden="true">
                  <path
                    v-for="feature in subregionFeatures"
                    :key="`${feature.code}-glow`"
                    :d="feature.path"
                    :class="['region-glow', hasSubregionPeriod(feature) ? changeTone(subregionPeriodChange(feature)) : 'unavailable']"
                    :style="{ stroke: subregionGlowColor(feature) }"
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
                      hasSubregionPeriod(feature) ? changeTone(subregionPeriodChange(feature)) : 'unavailable',
                      { active: selectedSubregion?.code === feature.code }
                    ]"
                    :data-testid="`subregion-shape-${feature.code}`"
                    :style="{ fill: subregionHeatColor(feature) }"
                    :aria-label="`${feature.name} ${subregionChangeLabel(feature)}`"
                    @click="selectSubregionFromMap(feature.code)"
                  />
                </g>
              </svg>
            </div>

            <div v-if="!selectedRegion" class="map-target-buttons" aria-label="시도 선택 버튼">
              <a
                v-for="feature in mapFeatures"
                :key="`${feature.target.id}-button`"
                class="map-target-link"
                :href="`/realestate/map/${feature.target.targetId}`"
                :style="labelButtonStyle(feature)"
                :data-testid="`map-target-${feature.target.id}`"
                :aria-label="`${feature.target.name} ${mapFeatureChangeLabel(feature.target)}`"
                @click.prevent="navigateToRegion(feature.target)"
              >
                <span @click.prevent.stop="navigateToRegion(feature.target)">{{ feature.target.name }}</span>
              </a>
            </div>

            <div
              v-else
              :class="[
                'map-target-buttons',
                'subregion-target-buttons',
                {
                  'is-clustered': showSubregionClusters,
                  'is-cluster-focused': focusedSubregionClusterLabel
                }
              ]"
              aria-label="하위 지역 선택 버튼"
            >
              <template v-if="showSubregionClusters">
                <button
                  v-for="cluster in subregionClusters"
                  :key="`${cluster.id}-cluster`"
                  class="subregion-cluster-button"
                  type="button"
                  :style="subregionClusterButtonStyle(cluster)"
                  :data-testid="`subregion-cluster-${cluster.id}`"
                  :aria-label="`${cluster.label} ${cluster.count}개 지역 상세 지도 보기`"
                  @click="focusSubregionCluster(cluster)"
                >
                  <span>{{ cluster.label }}</span>
                  <small>{{ cluster.count }}곳</small>
                </button>
              </template>
              <template v-else>
                <button
                  v-for="feature in subregionFeatures"
                  :key="`${feature.code}-button`"
                  type="button"
                  :class="{ active: selectedSubregion?.code === feature.code, unavailable: isSubregionUnavailable(feature) }"
                  :style="subregionButtonStyle(feature)"
                  :data-testid="`subregion-button-${feature.code}`"
                  :disabled="isSubregionUnavailable(feature)"
                  :aria-label="`${feature.name} ${subregionChangeLabel(feature)}`"
                  @click="selectSubregion(feature.code)"
                >
                  <span>{{ feature.name }}</span>
                </button>
              </template>
            </div>
          </div>
          <div class="map-zoom-controls" aria-label="지도 확대 축소">
            <button
              type="button"
              aria-label="지도 축소"
              :disabled="mapViewport.scale <= minMapZoom + 0.01"
              @click="adjustMapZoom('out')"
            >
              -
            </button>
            <span data-testid="map-zoom-percent">{{ mapZoomPercent }}</span>
            <button
              type="button"
              aria-label="지도 확대"
              :disabled="mapViewport.scale >= maxMapZoom - 0.01"
              @click="adjustMapZoom('in')"
            >
              +
            </button>
            <button
              type="button"
              aria-label="지도 확대 초기화"
              :disabled="!isMapZoomed"
              @click="resetMapViewport"
            >
              1:1
            </button>
          </div>
        </div>

        <div class="map-stage-footer">
          <article>
            <span>가장 높은 상승</span>
            <strong>{{ selectedRegion ? highestGainSubregion?.name ?? '수집 전' : highestGainRegion.name }}</strong>
            <em
              :class="
                selectedRegion && highestGainSubregion
                  ? changeTone(subregionPeriodChange(highestGainSubregion))
                  : changeTone(periodChange(highestGainRegion))
              "
            >
              {{
                selectedRegion && highestGainSubregion
                  ? formatChange(subregionPeriodChange(highestGainSubregion))
                  : formatChange(periodChange(highestGainRegion))
              }}
            </em>
          </article>
          <article>
            <span>가장 많은 하락</span>
            <strong>{{ selectedRegion ? largestDeclineSubregion?.name ?? '수집 전' : largestDeclineRegion.name }}</strong>
            <em
              :class="
                selectedRegion && largestDeclineSubregion
                  ? changeTone(subregionPeriodChange(largestDeclineSubregion))
                  : changeTone(periodChange(largestDeclineRegion))
              "
            >
              {{
                selectedRegion && largestDeclineSubregion
                  ? formatChange(subregionPeriodChange(largestDeclineSubregion))
                  : formatChange(periodChange(largestDeclineRegion))
              }}
            </em>
          </article>
          <article>
            <span>{{ selectedRegion ? '하위지역' : '지역 단위' }}</span>
            <strong>{{ selectedRegion ? `${subregionFeatures.length}개 구·시·군` : '17개 시도' }}</strong>
            <em data-testid="subregion-layer-status">{{ selectedRegion ? subregionLayerStatusText : '시도 기준' }}</em>
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
          <div class="map-report-heading">
            <p class="label">지역 리포트</p>
            <div class="map-report-title-row">
              <h3 id="map-report-title">{{ selectedReport.name }}</h3>
              <button
                class="watch-heart-button report-watch-button"
                :class="{ active: isSelectedRegionWatched }"
                type="button"
                :data-testid="selectedRegionWatchTestId"
                :aria-label="selectedRegionWatchLabel"
                :aria-pressed="isSelectedRegionWatched"
                @click="toggleSelectedRegionWatch"
              >{{ isSelectedRegionWatched ? '♥' : '♡' }}</button>
              <button
                v-if="selectedRegionChatAttachment"
                class="chat-attach-button report-chat-button"
                type="button"
                :data-testid="selectedRegionChatTestId"
                :aria-label="selectedRegionChatLabel"
                @click="attachSelectedRegionToChat"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M7 8.5h10" />
                  <path d="M7 12h6" />
                  <path d="M5.5 4.5h13A2.5 2.5 0 0 1 21 7v8a2.5 2.5 0 0 1-2.5 2.5H12L7 21v-3.5H5.5A2.5 2.5 0 0 1 3 15V7a2.5 2.5 0 0 1 2.5-2.5Z" />
                </svg>
              </button>
            </div>
            <span>{{ selectedRegion?.regionCode }} · {{ selectedReport.subregionCode }}</span>
          </div>
          <button class="icon-button" data-testid="close-map-report" type="button" aria-label="지역 리포트 닫기" @click="closeReport">
            ×
          </button>
        </div>

        <section class="map-briefing-report-layout" aria-label="선택 지역 요약 리포트">
          <article
            class="map-report-card featured"
            data-testid="report-section-ai-briefing"
            aria-labelledby="map-ai-briefing-label"
          >
            <div class="map-report-card-header">
              <div class="map-report-title-stack">
                <p id="map-ai-briefing-label">AI 핵심 브리핑</p>
              </div>
            </div>
            <div class="map-report-card-body">
              <div class="map-report-hero-grid">
                <div class="map-report-outlook-grid" aria-label="기대와 우려 요약">
                  <section class="map-report-outlook-panel expectation" aria-label="기대 지점">
                    <p>기대 지점</p>
                    <ul>
                      <li v-for="point in selectedReport.expectationPoints" :key="point" class="map-report-outlook-row">
                        {{ point }}
                      </li>
                    </ul>
                  </section>
                  <section class="map-report-outlook-panel concern" aria-label="우려 지점">
                    <p>우려 지점</p>
                    <ul>
                      <li v-for="point in selectedReport.concernPoints" :key="point" class="map-report-outlook-row">
                        {{ point }}
                      </li>
                    </ul>
                  </section>
                </div>
              </div>
            </div>
          </article>

          <section
            class="map-report-card analysis"
            data-testid="report-section-ai-analysis"
            aria-labelledby="map-briefing-analysis-title"
          >
            <div class="map-report-card-header">
              <div>
                <p>AI 분석 리포트</p>
                <h4 id="map-briefing-analysis-title">최신 종합 리포트</h4>
              </div>
              <span data-testid="report-updated-at">리포트 업데이트 {{ selectedReport.reportUpdatedAtLabel }}</span>
            </div>
            <div class="map-report-card-body map-report-analysis-copy">
              <div class="map-report-delta-block analysis-delta">
                <span>{{ periodLabelById[activePeriod] }}</span>
                <strong :class="['map-report-delta-value', changeTone(selectedReport.change)]">
                  {{ selectedReport.hasLivePeriod ? formatChange(selectedReport.change) : '자료 없음' }}
                </strong>
              </div>
              <div class="map-report-analysis-sections">
                <article
                  v-for="segment in selectedReport.analysisSegments"
                  :key="segment.key"
                  :class="['map-report-analysis-segment', { labeled: segment.label }]"
                >
                  <strong v-if="segment.label">{{ segment.label }}</strong>
                  <p>{{ segment.text }}</p>
                </article>
              </div>
            </div>
          </section>

          <section
            class="map-report-card sources"
            data-testid="report-section-related-reports"
            aria-labelledby="map-briefing-related-title"
          >
            <div class="map-report-card-header">
              <div>
                <p>관련 뉴스·리포트</p>
                <h4 id="map-briefing-related-title">근거 적재소</h4>
              </div>
              <span>{{ selectedReport.relatedReports.length }}개</span>
            </div>
            <div class="map-report-card-body map-related-report-ledger">
              <template v-for="item in selectedReport.relatedReports" :key="item.label">
                <a
                  v-if="item.url"
                  class="map-related-report-row"
                  :href="item.url"
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  <span>{{ item.label }}</span>
                  <strong>{{ item.title }}</strong>
                  <em>{{ item.meta }}</em>
                </a>
                <article v-else class="map-related-report-row">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.title }}</strong>
                  <em>{{ item.meta }}</em>
                </article>
              </template>
            </div>
          </section>
        </section>
      </aside>
    </section>
  </section>
</template>
