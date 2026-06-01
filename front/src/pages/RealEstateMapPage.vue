<script setup lang="ts">
import { geoCentroid, geoMercator, geoPath } from 'd3-geo';
import type { Feature, FeatureCollection, Geometry, Position } from 'geojson';
import { feature as topojsonFeature } from 'topojson-client';
import type { GeometryCollection, Topology } from 'topojson-specification';
import { computed, ref } from 'vue';

import mapFixture from '../fixtures/realestate-map-targets.json';
import koreaProvincesTopo from '../fixtures/skorea-provinces-2018-topo-simple.json';

type PeriodKey = 'week' | 'month' | 'halfYear';
type MapTarget = (typeof mapFixture.targets)[number];
type ProvinceProperties = {
  base_year: string;
  code: string;
  name: string;
  name_eng: string;
};
type ProvinceFeature = Feature<Geometry, ProvinceProperties>;
type KoreaTopology = Topology<{
  skorea_provinces_2018_geo: GeometryCollection<ProvinceProperties>;
}>;
type MapFeature = {
  code: string;
  label: { x: number; y: number };
  path: string;
  pathTransform?: string;
  provinceName: string;
  target: MapTarget;
};
type IssueCard = {
  detail: string;
  label: string;
  risk: string;
};

const periodOptions: { id: PeriodKey; label: string }[] = [
  { id: 'week', label: '1주' },
  { id: 'month', label: '1개월' },
  { id: 'halfYear', label: '6개월' }
];

const metricLabels = [
  ['가격 흐름', 'priceFlow'],
  ['거래 강도', 'tradeStrength'],
  ['전세 압력', 'jeonsePressure'],
  ['공급/청약', 'supplySignal'],
  ['정책/교통', 'policyEvent'],
  ['커뮤니티 반응', 'communityReaction']
] as const;

const activePeriod = ref<PeriodKey>('month');
const selectedTargetId = ref<string | null>(null);
const reportOpening = ref(false);
const reportSettled = ref(true);
let reportOpeningTimer: number | undefined;
let reportSettledTimer: number | undefined;
const targets = mapFixture.targets;
const mapSize = { width: 430, height: 630 };
const koreaTopology = koreaProvincesTopo as KoreaTopology;
const koreaFeatureCollection = topojsonFeature(
  koreaTopology,
  koreaTopology.objects.skorea_provinces_2018_geo
) as FeatureCollection<Geometry, ProvinceProperties>;
const OFFSHORE_POLYGON_AREA_THRESHOLD = 0.05;
const JEJU_VISUAL_OFFSET_Y = -56;
const polygonArea = (ring: Position[]) => {
  if (ring.length < 3) return 0;

  return Math.abs(
    ring.reduce((sum, point, index) => {
      const previous = ring[index === 0 ? ring.length - 1 : index - 1];

      return sum + (previous[0] * point[1] - point[0] * previous[1]);
    }, 0) / 2
  );
};
const trimOffshorePolygons = (feature: ProvinceFeature): ProvinceFeature => {
  if (feature.geometry.type !== 'MultiPolygon') return feature;

  const polygons = feature.geometry.coordinates.map((polygon) => ({
    area: polygonArea(polygon[0] ?? []),
    polygon
  }));
  const largestArea = Math.max(...polygons.map((polygon) => polygon.area));
  const visiblePolygons = polygons
    .filter((polygon) => polygon.area === largestArea || polygon.area >= OFFSHORE_POLYGON_AREA_THRESHOLD)
    .map((polygon) => polygon.polygon);

  return {
    ...feature,
    geometry: {
      ...feature.geometry,
      coordinates: visiblePolygons
    }
  };
};
const displayFeatureCollection: FeatureCollection<Geometry, ProvinceProperties> = {
  ...koreaFeatureCollection,
  features: koreaFeatureCollection.features.map((feature) => trimOffshorePolygons(feature as ProvinceFeature))
};
const countryOutlineFeatureCollection: FeatureCollection<Geometry, ProvinceProperties> = {
  ...displayFeatureCollection,
  features: displayFeatureCollection.features.filter((feature) => feature.properties.code !== '39')
};
const targetByRegionCode = new Map(targets.map((target) => [target.regionCode, target]));
const projection = geoMercator().fitSize([mapSize.width, mapSize.height], displayFeatureCollection);
const pathGenerator = geoPath(projection);
const countryPath = pathGenerator(countryOutlineFeatureCollection) ?? '';
const mapFeatures = displayFeatureCollection.features.reduce<MapFeature[]>((items, feature: ProvinceFeature) => {
  const target = targetByRegionCode.get(feature.properties.code);
  const path = pathGenerator(feature);
  const centroid = projection(geoCentroid(feature));

  if (!target || !path || !centroid) return items;

  const visualOffsetY = target.id === 'jeju' ? JEJU_VISUAL_OFFSET_Y : 0;

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

const selectedTarget = computed(() => targets.find((target) => target.id === selectedTargetId.value) ?? null);
const layoutMode = computed(() => (selectedTarget.value ? 'split' : 'centered'));
const strongestRegion = computed(() =>
  [...targets].sort(
    (left, right) => Math.abs(right.periodChanges[activePeriod.value]) - Math.abs(left.periodChanges[activePeriod.value])
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
const labelButtonStyle = (feature: MapFeature) => {
  const offset = labelOffsetByRegionId[feature.target.id] ?? { x: 0, y: 0 };

  return {
    left: `${((feature.label.x + offset.x) / mapSize.width) * 100}%`,
    top: `${((feature.label.y + offset.y - 4) / mapSize.height) * 100}%`,
    zIndex: compactRegionIds.has(feature.target.id) ? 4 : 2
  };
};
const issueCopy: Record<string, IssueCard> = {
  GTX: {
    label: '교통 기대',
    detail: 'GTX·광역 교통 키워드가 출퇴근 시간 단축 기대와 함께 확산됩니다.',
    risk: '노선·개통 시점 지연 리스크를 같이 봐야 합니다.'
  },
  전세: {
    label: '전세 압력',
    detail: '전세 매물 감소 체감과 전세가 방어 여부가 커뮤니티에서 반복됩니다.',
    risk: '실거래 공개 지연 때문에 호가 체감과 신고가를 분리해야 합니다.'
  },
  정비사업: {
    label: '정비사업 기대',
    detail: '재건축·재개발·정비구역 별칭이 늘며 장기 기대가 붙는 흐름입니다.',
    risk: '사업 단계가 낮은 기대성 언급은 가격 사실로 보지 않습니다.'
  },
  '대출 규제': {
    label: '정책 민감도',
    detail: '대출 한도와 금리 부담을 두고 관망 댓글이 가격 기대를 누릅니다.',
    risk: '정책 발표 전후로 반응이 급변할 수 있습니다.'
  },
  공급: {
    label: '공급 부담',
    detail: '입주 물량과 매물 누적 체감이 가격 반응을 약하게 만드는 축입니다.',
    risk: '권역 전체보다 생활권 단위로 쪼개야 합니다.'
  },
  매물: {
    label: '매물 체감',
    detail: '포털 매물 수와 현장 체감 사이의 간극을 확인해야 하는 구간입니다.',
    risk: '호가·매물 데이터는 출처 계약 전까지 신뢰도 표시가 필요합니다.'
  },
  교통: {
    label: '교통 이벤트',
    detail: '철도·도로·환승 개선 기대가 특정 생활권 언급량을 밀어 올립니다.',
    risk: '발표와 착공, 개통은 시장 반응 강도가 다릅니다.'
  },
  학군: {
    label: '학군 수요',
    detail: '학군·생활 인프라 키워드가 전세와 매매 반응을 같이 자극합니다.',
    risk: '계절성과 입학 시즌 효과를 분리해야 합니다.'
  },
  '입주 물량': {
    label: '입주 물량',
    detail: '신규 입주와 전세 매물 출회가 단기 체감에 크게 반영됩니다.',
    risk: '입주장 영향은 단지·동 단위 확인이 필요합니다.'
  },
  '표본 부족': {
    label: '표본 부족',
    detail: '거래 표본이 얇아 색상보다 stale·confidence badge를 먼저 봐야 합니다.',
    risk: '작은 변동률을 방향성으로 해석하지 않습니다.'
  }
};

const issueCard = (issue: string): IssueCard =>
  issueCopy[issue] ?? {
    label: issue,
    detail: `${issue} 키워드가 지역 반응의 설명 변수로 관찰됩니다.`,
    risk: '커뮤니티 반응과 시장 fact를 분리해서 확인해야 합니다.'
  };
const hasBatchim = (value: string) => {
  const lastCode = value.charCodeAt(value.length - 1) - 0xac00;

  return lastCode >= 0 && lastCode <= 11171 && lastCode % 28 !== 0;
};
const topicName = (value: string) => `${value}${hasBatchim(value) ? '은' : '는'}`;
const selectedIssueCards = computed(() => selectedTarget.value?.issues.map(issueCard) ?? []);
const reportPanelStyle = computed(() =>
  reportSettled.value
    ? {
        opacity: '1',
        transform: 'none',
        transition: 'none'
      }
    : undefined
);
const selectedCommunityPulse = computed(() => {
  if (!selectedTarget.value) return null;

  const target = selectedTarget.value;
  const change = Math.abs(periodChange(target));
  const mentionCount = Math.max(42, Math.round(target.sampleCount * (0.46 + change * 0.18)));
  const previousMentionCount = Math.max(18, Math.round(mentionCount / (1.18 + change * 0.36)));
  const mentionDeltaPct = Math.round(((mentionCount - previousMentionCount) / previousMentionCount) * 100);
  const primaryIssue = target.issues[0] ?? '지역 반응';
  const secondaryIssue = target.issues[1] ?? '시장 사실';

  return {
    sourceMix: [
      { label: '네이버 카페', value: '42%' },
      { label: '지역 블로그', value: '25%' },
      { label: '유튜브', value: '18%' },
      { label: '뉴스·정책', value: '15%' }
    ],
    title: mentionDeltaPct >= 30 ? '언급량 급증' : '언급량 증가',
    mentionCount,
    previousMentionCount,
    mentionDeltaPct,
    summary: `${topicName(target.name)} 최근 ${primaryIssue} 키워드가 먼저 튀었고, ${secondaryIssue} 이슈가 댓글과 영상 제목으로 이어지는 흐름입니다.`,
    bullets: [
      `${primaryIssue} 관련 별칭과 체감 표현이 반복되며 원문 후보가 늘었습니다.`,
      target.issues.includes('전세')
        ? '전세 매물 감소 체감이 가격 기대와 우려를 동시에 키우고 있습니다.'
        : `${secondaryIssue} 언급이 가격 방향보다 먼저 움직이는 선행 반응으로 보입니다.`,
      `현재 리포트는 표본 ${target.sampleCount}건, 신뢰도 ${target.confidence}% 기준의 관찰 요약입니다.`
    ]
  };
});

const selectTarget = (targetId: string) => {
  selectedTargetId.value = targetId;
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
  selectedTargetId.value = null;
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
</script>

<template>
  <section :class="['realestate-map-page', { 'has-report': selectedTarget }]" aria-labelledby="realestate-map-title">
    <header class="map-page-header">
      <div>
        <p class="eyebrow">regional heat layer · {{ mapFixture.mapDataSource }}</p>
        <h2 id="realestate-map-title">전국 지역 흐름 지도</h2>
        <p>실제 시도 경계 TopoJSON 위에 가격 흐름과 커뮤니티 반응을 입힌 3D 관제형 지도입니다.</p>
      </div>
      <div class="map-header-actions">
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
      aria-label="지도와 선택 지역 리포트"
    >
      <article class="realestate-map-stage" aria-labelledby="korea-map-title">
        <div class="map-stage-toolbar">
          <div>
            <p class="label">terrain heatmap</p>
            <h3 id="korea-map-title">Korea 3D Market Surface</h3>
          </div>
          <div class="map-legend" aria-label="지도 색상 범례">
            <span><i class="up"></i>상승</span>
            <span><i class="down"></i>하락</span>
            <span><i class="empty"></i>표본 부족</span>
          </div>
        </div>

        <div class="korea-map-shell">
          <div class="korea-map-board">
            <svg class="korea-region-map" viewBox="0 0 430 630" role="img" aria-label="전국 시도별 상승 하락 지도">
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
                  :class="[
                    'region-shape',
                    changeTone(periodChange(feature.target)),
                    { active: selectedTarget?.id === feature.target.id }
                  ]"
                  :style="{ fill: heatColor(periodChange(feature.target)) }"
                  :transform="feature.pathTransform"
                  :aria-label="`${feature.target.name} ${formatChange(periodChange(feature.target))}`"
                  @click="selectTarget(feature.target.id)"
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
            <div class="map-target-buttons" aria-label="지도 지역 선택 버튼">
              <button
                v-for="feature in mapFeatures"
                :key="`${feature.target.id}-button`"
                type="button"
                :class="{ active: selectedTarget?.id === feature.target.id }"
                :style="labelButtonStyle(feature)"
                :data-testid="`map-target-${feature.target.id}`"
                :aria-label="`${feature.target.name} ${formatChange(periodChange(feature.target))}`"
                @click="selectTarget(feature.target.id)"
              >
                <span>{{ feature.target.name }}</span>
              </button>
            </div>
          </div>
        </div>

        <div class="map-stage-footer">
          <article>
            <span>가장 강한 변화</span>
            <strong>{{ strongestRegion.name }}</strong>
            <em :class="changeTone(periodChange(strongestRegion))">{{ formatChange(periodChange(strongestRegion)) }}</em>
          </article>
          <article>
            <span>지도 단위</span>
            <strong>17개 시도</strong>
            <em>GeoJSON 교체 가능</em>
          </article>
          <article>
            <span>다음 단계</span>
            <strong>시군구 drilldown</strong>
            <em>단지 좌표 후속</em>
          </article>
        </div>
      </article>

      <aside
        v-if="selectedTarget && selectedCommunityPulse"
        :class="['map-report-panel', { opening: reportOpening }]"
        :style="reportPanelStyle"
        data-testid="map-report-panel"
        aria-labelledby="map-report-title"
      >
        <div class="map-report-header">
          <div>
            <p class="label">지역 리포트</p>
            <h3 id="map-report-title">{{ selectedTarget.name }}</h3>
            <span>{{ selectedTarget.regionCode }} · {{ selectedTarget.geometryId }}</span>
          </div>
          <button
            class="icon-button"
            data-testid="close-map-report"
            type="button"
            aria-label="지역 리포트 닫기"
            @click="closeReport"
          >
            ×
          </button>
        </div>

        <div class="report-lead">
          <strong :class="changeTone(periodChange(selectedTarget))">{{ formatChange(periodChange(selectedTarget)) }}</strong>
          <p>{{ selectedTarget.summary }}</p>
          <div>
            <span class="status-pill subtle">표본 {{ selectedTarget.sampleCount }}건</span>
            <span class="status-pill subtle">신뢰도 {{ selectedTarget.confidence }}%</span>
          </div>
        </div>

        <section class="community-pulse-board" aria-labelledby="community-pulse-title">
          <div class="report-section-title">
            <p class="label">community pulse</p>
            <h4 id="community-pulse-title">{{ selectedCommunityPulse.title }}</h4>
          </div>
          <div class="mention-delta-card">
            <strong>+{{ selectedCommunityPulse.mentionDeltaPct }}%</strong>
            <span>{{ selectedCommunityPulse.previousMentionCount }}건 → {{ selectedCommunityPulse.mentionCount }}건</span>
            <p>{{ selectedCommunityPulse.summary }}</p>
          </div>
          <div class="community-source-mix">
            <article v-for="source in selectedCommunityPulse.sourceMix" :key="source.label">
              <span>{{ source.label }}</span>
              <strong>{{ source.value }}</strong>
            </article>
          </div>
          <ul class="community-bullet-list">
            <li v-for="bullet in selectedCommunityPulse.bullets" :key="bullet">{{ bullet }}</li>
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
          <article v-for="[label, key] in metricLabels" :key="key">
            <span>{{ label }}</span>
            <strong>{{ selectedTarget.report[key] }}</strong>
          </article>
        </div>

        <section class="report-chip-section" aria-label="주요 쟁점">
          <span v-for="issue in selectedTarget.issues" :key="issue">{{ issue }}</span>
        </section>

        <section class="sample-complex-list" aria-labelledby="sample-complex-title">
          <div class="section-band-title compact">
            <p class="label">complex preview</p>
            <h4 id="sample-complex-title">후속 단지 레이어 후보</h4>
          </div>
          <article v-for="complex in selectedTarget.sampleComplexes" :key="complex">
            <strong>{{ complex }}</strong>
            <span>좌표·별칭 매핑 후 클릭 리포트 연결</span>
          </article>
        </section>
      </aside>
    </section>
  </section>
</template>
