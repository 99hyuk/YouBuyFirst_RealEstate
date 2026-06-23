<script setup lang="ts">
import { geoContains, geoMercator, geoPath } from 'd3-geo';
import type { Feature, FeatureCollection, GeoJsonProperties, Geometry, Position } from 'geojson';
import { feature as topojsonFeature } from 'topojson-client';
import type { GeometryCollection, Topology } from 'topojson-specification';
import { computed, onMounted, reactive, ref, shallowRef, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import mapFixture from '../fixtures/realestate-map-targets.json';
import municipalityTopologyUrl from '../fixtures/skorea-municipalities-2018-topo-simple.json?url';
import koreaProvincesTopo from '../fixtures/skorea-provinces-2018-topo-simple.json';
import {
  fetchRealEstateMapLayer,
  type PeriodKey,
  type RealEstateMapLayerPeriod,
  type RealEstateMapLayerResponse,
  type RealEstateMapLayerTarget
} from '../lib/realestate-map';
import {
  fetchRealEstateTargetEvidenceLogs,
  type RealEstateEvidenceItem,
  type RealEstateEvidenceLog
} from '../lib/realestate-evidence-logs';

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
  provider?: string | null;
  sourceLabel?: string | null;
  stale?: boolean;
  targetId: string;
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
type IssueCard = {
  detail: string;
  label: string;
  risk: string;
};

const route = useRoute();
const router = useRouter();

const periodOptions: { id: PeriodKey; label: string }[] = [
  { id: 'month', label: '1개월' },
  { id: 'quarter', label: '3개월' },
  { id: 'halfYear', label: '6개월' }
];
const periodLabelById: Record<PeriodKey, string> = {
  month: '최근 1개월',
  quarter: '최근 3개월',
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
const selectedSubregionClusterId = ref<string | null>(null);
const reportOpening = ref(false);
const reportSettled = ref(true);
let reportOpeningTimer: number | undefined;
let reportSettledTimer: number | undefined;

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
// 선택한 시군구(있으면) 또는 시도 기준으로 해당 지역 실거래 지도로 이동하는 링크.
const transactionMapLink = computed(() => {
  const code = selectedSubregion.value?.code ?? selectedRegion.value?.regionCode ?? '';
  return code ? `/realestate/complexes?region=${code}` : '/realestate/complexes';
});
const transactionMapLabel = computed(() => {
  if (selectedSubregion.value) return `${selectedSubregion.value.name} 실거래 지도`;
  if (selectedRegion.value) return `${selectedRegion.value.name} 실거래 지도`;
  return '실거래 지도';
});
const strongestRegion = computed(() =>
  [...targets].sort(
    (left, right) => Math.abs(right.periodChanges[activePeriod.value]) - Math.abs(left.periodChanges[activePeriod.value])
  )[0]
);
const strongestSubregion = computed(() =>
  [...subregionFeatures.value.filter((feature) => hasSubregionPeriod(feature))].sort(
    (left, right) =>
      Math.abs(subregionPeriodChange(right, activePeriod.value)) - Math.abs(subregionPeriodChange(left, activePeriod.value))
  )[0] ?? null
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
const subregionLayerPeriod = (feature: SubregionFeature, period: PeriodKey = activePeriod.value) =>
  subregionLayerByCode.value.get(feature.code)?.periods?.[period] ?? null;
const effectiveSubregionPeriod = (feature: SubregionFeature, period: PeriodKey = activePeriod.value) =>
  usableMapPeriod(subregionLayerPeriod(feature, period));
const hasSubregionPeriod = (feature: SubregionFeature, period: PeriodKey = activePeriod.value) =>
  Boolean(effectiveSubregionPeriod(feature, period));
const isSubregionUnavailable = (feature: SubregionFeature) => !hasSubregionPeriod(feature);
const formatChange = (value: number) => `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
const formatEvidenceConfidence = (value?: number | null) => `${Math.round((value ?? 0) * 100)}%`;
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
const changeTone = (value: number) => {
  if (value > 0.04) return 'up';
  if (value < -0.04) return 'down';
  return 'flat';
};
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
const heatColor = (value: number) => {
  const intensity = Math.min(1, Math.max(0.12, Math.abs(value) / 0.65));
  if (value > 0.04) return `rgba(255, 54, 88, ${0.3 + intensity * 0.66})`;
  if (value < -0.04) return `rgba(42, 125, 255, ${0.28 + intensity * 0.62})`;
  return 'rgba(126, 143, 166, 0.42)';
};
const unpublishedHeatColor = 'rgba(10, 15, 24, 0.82)';
const unpublishedGlowColor = 'rgba(4, 8, 14, 0.72)';
const missingHeatColor = 'rgba(126, 143, 166, 0.18)';
const subregionPeriodChange = (feature: SubregionFeature, period: PeriodKey = activePeriod.value) => {
  const livePeriod = effectiveSubregionPeriod(feature, period);
  if (livePeriod) return livePeriod.changePct;
  return 0;
};
const subregionSampleCount = (feature: SubregionFeature) => {
  const livePeriod = effectiveSubregionPeriod(feature);
  if (livePeriod) return livePeriod.sampleCount;
  return 0;
};
const subregionConfidence = (feature: SubregionFeature) =>
  effectiveSubregionPeriod(feature)?.confidence ?? 0;
const labelButtonStyle = (feature: MapFeature) => ({
  left: `${((feature.label.x + (labelNudgeByRegionId[feature.target.id]?.x ?? 0)) / nationalMapSize.width) * 100}%`,
  top: `${((feature.label.y + (labelNudgeByRegionId[feature.target.id]?.y ?? 0)) / nationalMapSize.height) * 100}%`
});
const subregionButtonStyle = (feature: SubregionFeature) => ({
  left: `${(feature.label.x / detailMapSize.width) * 100}%`,
  top: `${(feature.label.y / detailMapSize.height) * 100}%`
});
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
const subregionClusterButtonStyle = (cluster: SubregionCluster) => ({
  left: `${((cluster.center.x + (subregionClusterNudgeById[cluster.id]?.x ?? 0)) / detailMapSize.width) * 100}%`,
  top: `${((cluster.center.y + (subregionClusterNudgeById[cluster.id]?.y ?? 0)) / detailMapSize.height) * 100}%`
});
const firstPeriod = (periods: Partial<Record<PeriodKey, RealEstateMapLayerPeriod>>) =>
  periods.month ?? periods.quarter ?? periods.halfYear ?? Object.values(periods)[0] ?? null;
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
  return period ? heatColor(period.changePct) : unpublishedHeatColor;
};
const subregionGlowColor = (feature: SubregionFeature) =>
  hasSubregionPeriod(feature) ? subregionHeatColor(feature) : unpublishedGlowColor;
const subregionRepresentativePeriod = computed(() => {
  for (const layerTarget of subregionLayerByCode.value.values()) {
    const period = layerTarget.periods?.[activePeriod.value] ?? firstPeriod(layerTarget.periods ?? {});
    if (period) return period;
  }

  return null;
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
const refreshSubregionMapLayer = async (region: MapTarget | null) => {
  if (!region) {
    subregionLayerByCode.value = new Map();
    subregionLayerLoadState.value = 'idle';
    return;
  }

  subregionLayerLoadState.value = 'loading';
  try {
    const layer = await fetchRealEstateMapLayer({ layerType: 'sigungu', parentTargetId: region.targetId });
    subregionLayerByCode.value = new Map(layer.targets.map((target) => [target.regionCode, target]));
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

  const period = subregionRepresentativePeriod.value;
  if (period) {
    const provider = mapSourceLabel(period.provider ?? period.sourceLabel);
    const status = mapDataStatusLabel(period.dataStatus);
    const freshness = period.stale ? '갱신 지연' : '최신 반영';
    const asOf = formatMapTimestamp(period.asOf);
    return `${provider} · ${status} · ${freshness} · ${asOf}`;
  }

  return '하위 레이어 수집 전/insufficient';
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
    detail: '거래 표본이 얇아 색상보다 갱신 지연·신뢰도 배지를 먼저 봐야 합니다.',
    risk: '작은 변동률을 방향성으로 해석하지 않습니다.'
  }
};
const issueCard = (issue: string): IssueCard =>
  issueCopy[issue] ?? {
    label: issue,
    detail: `${issue} 이슈가 지역 반응의 설명 변수로 관찰됩니다.`,
    risk: '커뮤니티 반응과 시장 사실을 분리해서 확인해야 합니다.'
  };
const selectedIssueCards = computed(() => selectedReport.value?.issues.map(issueCard) ?? []);
const selectedEvidenceLayerTarget = computed(() =>
  selectedSubregion.value ? subregionLayerByCode.value.get(selectedSubregion.value.code) ?? null : null
);
const selectedEvidenceTargetId = computed(() =>
  selectedEvidenceLayerTarget.value?.targetId ?? selectedRegion.value?.targetId ?? null
);
const latestMapEvidenceLog = computed(() => mapEvidenceLogs.value[0] ?? null);
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
  const subjectName = feature?.name ?? target.name;
  const subjectCode = feature?.code ?? target.regionCode;
  const change = feature ? subregionPeriodChange(feature) : periodChange(target);
  const sampleCount = feature ? subregionSampleCount(feature) : targetSampleCount(target);
  const confidence = feature ? subregionConfidence(feature) : targetConfidence(target);
  const confidencePct = Math.round(confidence * 100);
  const directSubregionPeriod = feature ? usableMapPeriod(subregionLayerPeriod(feature)) : null;
  const livePeriod = feature ? effectiveSubregionPeriod(feature) : usableMapPeriod(targetPeriodMeta(target));
  const hasLivePeriod = Boolean(livePeriod);
  const isDerivedSubregionPeriod = Boolean(feature && livePeriod && !directSubregionPeriod);
  const layerStatus = livePeriod
    ? `${mapSourceLabel(livePeriod.provider ?? livePeriod.sourceLabel)} · ${mapDataStatusLabel(livePeriod.dataStatus)} · ${livePeriod.stale ? '갱신 지연' : '최신 반영'}`
    : '시장 사실 수집 전/insufficient';
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
      : ['시장 사실 수집 전', 'AI 근거 확인 필요'];
  const primaryIssue = reportIssues[0] ?? '지역 반응';
  const secondaryIssue = reportIssues[1] ?? '시장 사실';
  const insufficientValue = '수집 전/insufficient';

  return {
    change,
    confidence: confidencePct,
    hasLivePeriod,
    mentionCount,
    mentionDeltaPct,
    previousMentionCount,
    issues: reportIssues,
    metrics: [
      { label: '가격 흐름', value: hasLivePeriod ? `${periodLabelById[activePeriod.value]} ${formatChange(change)}` : insufficientValue },
      { label: '거래 강도', value: hasLivePeriod ? `표본 ${sampleCount}건, ${change > 0 ? '관심 증가' : '관망 우세'}` : insufficientValue },
      { label: '전세 압력', value: latestMapEvidenceLog.value ? 'AI 근거 항목 확인' : insufficientValue },
      { label: '공급/청약', value: latestMapEvidenceLog.value ? 'AI 근거 항목 확인' : insufficientValue },
      { label: '정책/교통', value: latestMapEvidenceLog.value ? 'AI 근거 항목 확인' : insufficientValue },
      { label: '커뮤니티 언급', value: hasLivePeriod ? `언급 ${mentionCount}건, 전 구간 대비 +${mentionDeltaPct}%` : insufficientValue }
    ],
    name: feature ? `${target.name} ${subjectName}` : `${target.name} 전체`,
    sampleCount,
    sourceMix: [
      { label: '출처', value: livePeriod ? mapSourceLabel(livePeriod.provider ?? livePeriod.sourceLabel) : insufficientValue },
      { label: '수집 상태', value: mapDataStatusLabel(livePeriod?.dataStatus) ?? insufficientValue },
      { label: '기준 시각', value: formatMapTimestamp(livePeriod?.asOf) },
      { label: '갱신 상태', value: livePeriod ? (isDerivedSubregionPeriod ? '상위 지역 기반' : livePeriod.stale ? '갱신 지연' : '최신 반영') : '수집 전' }
    ],
    summary: hasLivePeriod
      ? `${subjectName} 지역은 ${target.name} 안에서 ${primaryIssue}, ${secondaryIssue} 흐름이 함께 관찰되는 지역입니다. 현재 지도 레이어는 ${layerStatus} 상태라 방향성과 표본 신뢰도를 함께 봅니다.${isDerivedSubregionPeriod ? ' 아직 시군구 직접 지표가 없어 상위 지역 반응을 하위 구역에 분산해 보여주는 임시 레이어입니다.' : ''}`
      : `${subjectName} 지도 흐름 자료는 아직 수집 전입니다. 이 구간은 값을 임의 추정하지 않고, 상위 지역 AI 근거와 하위 지역 갱신 배치가 연결되면 실제 리포트로 전환됩니다.`,
    title: change >= 0 ? '언급량 급증' : '우려 언급량 급증',
    mentionSummary: hasLivePeriod
      ? `${subjectName} 관련 커뮤니티 언급이 선택 기간에 빠르게 늘었습니다.`
      : `${subjectName} 언급 자료는 아직 수집 전/insufficient 상태입니다.`,
    bullets: hasLivePeriod
      ? [
          `${subjectName} 관련 언급은 ${previousMentionCount}건에서 ${mentionCount}건으로 늘었습니다.`,
          `${primaryIssue} 키워드가 먼저 움직이고, ${secondaryIssue} 이슈가 댓글 맥락에서 반복됩니다.`,
          `신뢰도 ${confidencePct}% 기준의 관찰 요약이며, ${isDerivedSubregionPeriod ? '시군구 직접값이 아니라 상위 지역 기반 보정값입니다.' : '출처와 기준 시각을 함께 확인해야 합니다.'}`
        ]
      : [
          `${subjectName} 지도 흐름과 커뮤니티 반응 자료는 아직 충분하지 않습니다.`,
          `${target.name} 상위 지역 AI 근거가 있으면 우선 표시하고, 하위 구간 값은 임의로 채우지 않습니다.`,
          '공공데이터, 반응 지표, 근거 링크가 연결되면 이 패널은 실제 수치 리포트로 전환됩니다.'
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
  },
  { immediate: true }
);
onMounted(() => {
  void refreshNationalMapLayer();
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
      <div class="map-header-actions">
        <RouterLink
          v-if="selectedRegion"
          class="transaction-map-cta"
          :to="transactionMapLink"
          data-testid="region-transaction-map-link"
        >
          🗺️ {{ transactionMapLabel }}
        </RouterLink>
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
          <div class="map-toolbar-right">
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
                  :style="{ stroke: usableMapPeriod(targetPeriodMeta(feature.target)) ? heatColor(periodChange(feature.target)) : missingHeatColor }"
                />
              </g>
              <g>
                <path
                  v-for="feature in mapFeatures"
                  :key="feature.target.id"
                  :d="feature.path"
                  :class="['region-shape', changeTone(periodChange(feature.target))]"
                  :style="{ fill: usableMapPeriod(targetPeriodMeta(feature.target)) ? heatColor(periodChange(feature.target)) : missingHeatColor }"
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
            <em data-testid="subregion-layer-status">{{ selectedRegion ? subregionLayerStatusText : '지도 흐름 자료 우선' }}</em>
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

        <section class="issue-report-section map-ai-report-section" aria-labelledby="map-ai-report-title">
          <div class="report-section-title">
            <p class="label">AI evidence</p>
            <h4 id="map-ai-report-title">지역 AI 근거 리포트</h4>
            <span>{{ mapEvidenceStatusText }}</span>
          </div>
          <article v-if="latestMapEvidenceLog" class="map-ai-report-card">
            <strong>{{ displayMapEvidenceCopy(latestMapEvidenceLog.subtitle) || '근거 기반 지역 평가' }}</strong>
            <p>{{ displayMapEvidenceCopy(latestMapEvidenceLog.summary) }}</p>
            <div>
              <span class="status-pill subtle">{{ latestMapEvidenceLog.modelName || '모델 확인 필요' }}</span>
              <span class="status-pill subtle">{{ mapEvidenceQualityLabel(latestMapEvidenceLog.dataQuality) }}</span>
              <span class="status-pill subtle">신뢰 {{ formatEvidenceConfidence(latestMapEvidenceLog.confidence) }}</span>
            </div>
            <ul v-if="visibleMapEvidenceItems.length" class="community-bullet-list">
              <li v-for="item in visibleMapEvidenceItems" :key="item.evidenceItemId">
                {{ item.label }} · {{ item.valueText || item.evidenceType || '값 확인 필요' }}
              </li>
            </ul>
          </article>
          <p v-else class="newsroom-empty-state">
            {{ mapEvidenceStatusText }} 상태입니다. 크롤링, 최근 이슈, AI 평가 배치가 해당 지역 근거를 만들면 이곳에 표시됩니다.
          </p>
        </section>

        <section class="community-pulse-board" aria-labelledby="community-pulse-title">
          <div class="report-section-title">
            <p class="label">community pulse</p>
            <h4 id="community-pulse-title">{{ selectedReport.title }}</h4>
          </div>
          <div class="mention-delta-card">
            <strong>{{ selectedReport.hasLivePeriod ? `+${selectedReport.mentionDeltaPct}%` : '수집 전' }}</strong>
            <span>{{ selectedReport.previousMentionCount }}건 → {{ selectedReport.mentionCount }}건</span>
            <p>{{ selectedReport.mentionSummary }}</p>
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
          <p v-if="!selectedReport.previewComplexes.length" class="newsroom-empty-state">
            단지 좌표와 alias 매핑이 아직 수집 전/insufficient 상태입니다.
          </p>
        </section>
      </aside>
    </section>
  </section>
</template>
