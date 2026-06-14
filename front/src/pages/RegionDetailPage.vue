<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import {
  buildNewsroomFeedItems,
  fetchRealEstateTargetContent,
  type NewsroomFeedItem
} from '../lib/realestate-content';
import { fetchRealEstateNearbyComplexes } from '../lib/realestate-complex-map';
import {
  fetchRealEstateTargetEvidenceLogs,
  type RealEstateEvidenceLog
} from '../lib/realestate-evidence-logs';
import {
  fetchRealEstateTargetTimeline,
  type RealEstateTimelineEvent
} from '../lib/realestate-timeline';
import KakaoComplexMap, { type ComplexMapMarker } from '../components/KakaoComplexMap.vue';

type DetailTone = 'up' | 'down' | 'flat';

type RealEstateTarget = {
  targetId: string;
  targetType: 'region' | 'living_area' | 'complex';
  name: string;
  region: string;
  headline: string;
  summary: string;
  indexChange: string;
  tradeVolume: string;
  jeonseRatio: string;
  supplySignal: string;
  confidence: string;
  tone: DetailTone;
  keywords: string[];
  metrics: { label: string; value: string; note: string; tone: DetailTone }[];
  reactions: { source: string; mentions: number; positive: number; negative: number; note: string }[];
  timeline: TimelineItem[];
  evidence: EvidenceLink[];
  mapCenter?: { lat: number; lng: number };
  mapLevel?: number;
  preferredMapTargetId?: string;
  mapMarkers?: ComplexMapMarker[];
};

type TimelineItem = {
  id?: string;
  time: string;
  title: string;
  detail: string;
  meta?: string;
};

type EvidenceLink = {
  label: string;
  source: string;
  url: string;
  meta?: string;
  statusLabel?: string;
};

const route = useRoute();

const mapoComplexMarkers: ComplexMapMarker[] = [
  {
    targetId: 'complex-mapo-raemian-prugio',
    name: '마포래미안푸르지오',
    address: '서울 마포구 아현동 일대',
    region: '서울 마포',
    lat: 37.5536,
    lng: 126.9564,
    tone: 'up',
    price: '15.3억',
    change: '+0.21%',
    reaction: '학군·역세권 언급 증가',
    provider: 'front fixture',
    asOf: '2026-06-13',
    dataStatus: 'mock 좌표',
    note: '실제 단지 좌표 DB 연결 전, 상세 지도 UX 검증용 marker입니다.'
  },
  {
    targetId: 'complex-gongdeok-xi',
    name: '공덕자이',
    address: '서울 마포구 공덕동 일대',
    region: '서울 마포',
    lat: 37.5452,
    lng: 126.9508,
    tone: 'flat',
    price: '14.8억',
    change: '+0.03%',
    reaction: '전세 매물 확인 필요',
    provider: 'front fixture',
    asOf: '2026-06-13',
    dataStatus: 'mock 좌표',
    note: '단지 provider key와 실거래 API 매핑 전 후보 marker입니다.'
  },
  {
    targetId: 'complex-ahyeon-raemian',
    name: '아현래미안',
    address: '서울 마포구 아현동 일대',
    region: '서울 마포',
    lat: 37.5571,
    lng: 126.9518,
    tone: 'down',
    price: '13.9억',
    change: '-0.06%',
    reaction: '가격 부담·전세 우려 혼재',
    provider: 'front fixture',
    asOf: '2026-06-13',
    dataStatus: 'mock 좌표',
    note: '반응/시장 fact 연결 전 주변 비교용 marker입니다.'
  }
];

const dongtanComplexMarkers: ComplexMapMarker[] = [
  {
    targetId: 'complex-dongtan-lotte-castle',
    name: '동탄역 롯데캐슬',
    address: '경기 화성시 동탄역권 일대',
    region: '경기 동탄',
    lat: 37.1991,
    lng: 127.0986,
    tone: 'up',
    price: '12.2억',
    change: '+0.19%',
    reaction: 'GTX·역세권 언급 증가',
    provider: 'front fixture',
    asOf: '2026-06-13',
    dataStatus: 'mock 좌표',
    note: '카카오 지도 내장과 리포트 패널 상호작용 검증용 marker입니다.'
  },
  {
    targetId: 'complex-dongtan-station-prugio',
    name: '동탄역 푸르지오',
    address: '경기 화성시 오산동 일대',
    region: '경기 동탄',
    lat: 37.2021,
    lng: 127.0943,
    tone: 'flat',
    price: '10.6억',
    change: '+0.02%',
    reaction: '교통 기대와 입주 우려 혼조',
    provider: 'front fixture',
    asOf: '2026-06-13',
    dataStatus: 'mock 좌표',
    note: '실제 단지 좌표와 provider key 연결 전 후보 marker입니다.'
  },
  {
    targetId: 'complex-dongtan-ubora',
    name: '동탄역 반도유보라',
    address: '경기 화성시 동탄역권 일대',
    region: '경기 동탄',
    lat: 37.1955,
    lng: 127.1021,
    tone: 'down',
    price: '9.7억',
    change: '-0.08%',
    reaction: '입주 물량·전세 매물 우려',
    provider: 'front fixture',
    asOf: '2026-06-13',
    dataStatus: 'mock 좌표',
    note: '공급/전세 지표와 같이 대조할 후보 marker입니다.'
  }
];

const targets: RealEstateTarget[] = [
  {
    targetId: 'region-seoul-mapo',
    targetType: 'region',
    name: '마포구 아파트',
    region: '서울',
    headline: '전세 매물 체감과 학군 키워드가 같이 움직입니다',
    summary: '공덕·아현 생활권 중심으로 전세 우려와 학군 기대가 동시에 관찰됩니다. 실거래 공개 지연이 있어 가격 판단은 보조 지표로만 둡니다.',
    indexChange: '+0.55%',
    tradeVolume: '42건',
    jeonseRatio: '64.8%',
    supplySignal: '입주 부담 낮음',
    confidence: '82%',
    tone: 'up',
    keywords: ['전세', '공덕', '학군', '역세권'],
    metrics: [
      { label: '매매가격지수', value: '102.1', note: '서울 평균보다 강함', tone: 'up' },
      { label: '전세가격지수', value: '101.4', note: '전세 압력 상승', tone: 'up' },
      { label: '거래량', value: '42건', note: '평년 대비 보통', tone: 'flat' },
      { label: '전세가율', value: '64.8%', note: '매매 전환 압력 후보', tone: 'up' }
    ],
    reactions: [
      { source: '네이버 카페', mentions: 58, positive: 46, negative: 34, note: '전세 매물 체감 댓글 반복' },
      { source: '지역 블로그', mentions: 31, positive: 52, negative: 21, note: '학군·역세권 후기 증가' },
      { source: '유튜브 댓글', mentions: 22, positive: 39, negative: 37, note: '가격 부담 논쟁' }
    ],
    timeline: [
      { time: '09:20', title: '전세 우려 급증', detail: '전세 매물 감소 체감 댓글이 30분 전 대비 +18%' },
      { time: '09:46', title: '공덕 키워드 확산', detail: '역세권·학군 키워드가 지역 블로그에 동시 등장' },
      { time: '10:05', title: '실거래 지연 표시', detail: '공공데이터 공개 지연 가능성을 stale로 유지' },
      { time: '10:14', title: '관심 지역 알림 후보', detail: '전세가율과 커뮤니티 반응이 같은 방향' }
    ],
    evidence: [
      { label: '실거래 공개 시스템', source: '국토교통부', url: 'https://rt.molit.go.kr/' },
      { label: '가격동향 통계', source: '한국부동산원', url: 'https://www.reb.or.kr/' },
      { label: '원문 후보 묶음', source: '네이버 카페', url: 'https://section.cafe.naver.com/' }
    ],
    mapCenter: { lat: 37.5536, lng: 126.9564 },
    mapLevel: 5,
    preferredMapTargetId: 'complex-mapo-raemian-prugio',
    mapMarkers: mapoComplexMarkers
  },
  {
    targetId: 'living-area-gyeonggi-dongtan-station',
    targetType: 'living_area',
    name: '동탄역권',
    region: '경기',
    headline: 'GTX 기대와 입주 물량 우려가 동시에 붙었습니다',
    summary: '교통 호재 반응은 강하지만 입주 물량과 전세 매물 우려가 같이 올라와 지표와 원문을 분리해 봐야 합니다.',
    indexChange: '+0.31%',
    tradeVolume: '57건',
    jeonseRatio: '58.2%',
    supplySignal: '입주 물량 확인',
    confidence: '74%',
    tone: 'flat',
    keywords: ['GTX', '입주', '전세', '역세권'],
    metrics: [
      { label: '매매가격지수', value: '100.7', note: '완만한 상승', tone: 'up' },
      { label: '전세수급지수', value: '106.1', note: '전세 수요 우위', tone: 'up' },
      { label: '준공 물량', value: '높음', note: '공급 부담 확인', tone: 'down' },
      { label: '거래량', value: '57건', note: '관심 대비 실제 거래는 보통', tone: 'flat' }
    ],
    reactions: [
      { source: '다음 카페', mentions: 42, positive: 44, negative: 39, note: 'GTX 기대와 입주 우려가 공존' },
      { source: '유튜브 댓글', mentions: 25, positive: 51, negative: 26, note: '교통 호재 영상 반응' },
      { source: '지역 블로그', mentions: 18, positive: 36, negative: 42, note: '전세 매물 논쟁' }
    ],
    timeline: [
      { time: '09:35', title: 'GTX 키워드 상승', detail: '동탄역권 언급이 카페 상위권 도달' },
      { time: '09:57', title: '입주 물량 언급 증가', detail: '전세 우려 댓글이 기대 반응을 상쇄' },
      { time: '10:08', title: '공공데이터 stale', detail: '실거래 신고 공개 지연 가능성 표시' },
      { time: '10:17', title: '확인 필요', detail: '전세수급지수와 입주 물량을 같이 대조' }
    ],
    evidence: [
      { label: '교통 정책 자료', source: '국토교통부', url: 'https://www.molit.go.kr/' },
      { label: '전월세 신고 데이터', source: '공공데이터포털', url: 'https://www.data.go.kr/' },
      { label: '지역 커뮤니티 원문', source: '다음 카페', url: 'https://top.cafe.daum.net/' }
    ],
    mapCenter: { lat: 37.1991, lng: 127.0986 },
    mapLevel: 5,
    preferredMapTargetId: 'complex-dongtan-lotte-castle',
    mapMarkers: dongtanComplexMarkers
  },
  {
    targetId: 'complex-mapo-raemian-prugio',
    targetType: 'complex',
    name: '마포래미안푸르지오',
    region: '서울 마포',
    headline: '학군·역세권 언급은 늘었지만 전세 체감은 분리 확인이 필요합니다',
    summary: '단지명과 마래푸 별칭이 같이 언급되는 구간입니다. 좌표와 가격은 아직 fixture 기준이므로 실제 provider 연결 전까지 mock 상태를 유지합니다.',
    indexChange: '+0.21%',
    tradeVolume: '18건',
    jeonseRatio: '66.1%',
    supplySignal: '주변 입주 부담 낮음',
    confidence: '78%',
    tone: 'up',
    keywords: ['마래푸', '학군', '공덕', '전세'],
    metrics: [
      { label: '실거래 흐름', value: '+0.21%', note: 'mock 단지 흐름', tone: 'up' },
      { label: '전세가율', value: '66.1%', note: '전세 체감 대조 필요', tone: 'up' },
      { label: '언급량', value: '44건', note: '단지군 TOP 3', tone: 'up' },
      { label: '좌표 상태', value: 'mock', note: 'SDK prototype marker', tone: 'flat' }
    ],
    reactions: [
      { source: '네이버 카페', mentions: 26, positive: 48, negative: 31, note: '마래푸 별칭과 학군 언급 반복' },
      { source: '지역 블로그', mentions: 11, positive: 52, negative: 22, note: '공덕·아현 생활권 후기' },
      { source: '유튜브 댓글', mentions: 7, positive: 39, negative: 36, note: '가격 부담과 전세 논쟁' }
    ],
    timeline: [
      { time: '09:32', title: '단지 별칭 감지', detail: '마래푸·마포래미안푸르지오 alias가 같은 target 후보로 묶임' },
      { time: '09:50', title: '학군 키워드 반복', detail: '지역 블로그와 카페에서 학군·역세권 키워드가 동시 등장' },
      { time: '10:04', title: '전세 체감 확인 필요', detail: '전세 매물 감소 표현은 원문과 실거래 공개 지연을 분리해 봄' },
      { time: '10:16', title: '지도 marker prototype', detail: '카카오맵 SDK 연결 전 mock 좌표 상태를 화면에 표시' }
    ],
    evidence: [
      { label: '단지 실거래 공개 시스템', source: '국토교통부', url: 'https://rt.molit.go.kr/' },
      { label: '단지 가격동향 확인 후보', source: '한국부동산원', url: 'https://www.reb.or.kr/' },
      { label: '마래푸 원문 후보', source: '네이버 카페', url: 'https://section.cafe.naver.com/' }
    ],
    mapCenter: { lat: 37.5536, lng: 126.9564 },
    mapLevel: 4,
    preferredMapTargetId: 'complex-mapo-raemian-prugio',
    mapMarkers: mapoComplexMarkers
  }
];

const routeTargetId = computed(() => String(route.params.targetId ?? '').trim());
const target = computed(() => targets.find((item) => item.targetId === routeTargetId.value));
const selectedMapMarkerId = ref('');
const apiMapMarkers = ref<ComplexMapMarker[]>([]);
const mapMarkerLoadState = ref<'loading' | 'live' | 'fallback'>('loading');
const confidenceValue = computed(() => (target.value ? Number.parseInt(target.value.confidence, 10) : 0));
const evidenceLinks = ref<EvidenceLink[]>([]);
const evidenceLoadState = ref<'loading' | 'live' | 'fallback'>('loading');
const timelineItems = ref<TimelineItem[]>([]);
const timelineLoadState = ref<'loading' | 'live' | 'fallback'>('loading');
const agentEvidenceLogs = ref<RealEstateEvidenceLog[]>([]);
const agentEvidenceLoadState = ref<'loading' | 'live' | 'fallback'>('loading');
const targetEvidence = computed(() => (
  evidenceLoadState.value === 'live' ? evidenceLinks.value : target.value?.evidence ?? []
));
const evidenceStatusLabel = computed(() => {
  if (evidenceLoadState.value === 'live') return 'content API 반영';
  if (evidenceLoadState.value === 'loading') return 'content API 확인 중';
  return '원문 확인 필요';
});
const targetMapMarkers = computed(() => (
  mapMarkerLoadState.value === 'live' ? apiMapMarkers.value : target.value?.mapMarkers ?? []
));
const mapMarkerSourceStatusLabel = computed(() => {
  if (mapMarkerLoadState.value === 'live') return 'marker API 반영';
  if (mapMarkerLoadState.value === 'loading') return 'marker API 확인 중';
  return 'fixture fallback';
});
const targetTimeline = computed(() => (
  timelineLoadState.value === 'live' ? timelineItems.value : target.value?.timeline ?? []
));
const timelineSourceStatusLabel = computed(() => {
  if (timelineLoadState.value === 'live') return 'timeline API 반영';
  if (timelineLoadState.value === 'loading') return 'timeline API 확인 중';
  return 'fixture fallback';
});
const agentEvidenceStatusLabel = computed(() => {
  if (agentEvidenceLoadState.value === 'live') return 'EvidenceLog API 반영';
  if (agentEvidenceLoadState.value === 'loading') return 'EvidenceLog API 확인 중';
  return '근거 로그 대기';
});
const mapCenter = computed(() => {
  const firstMarker = targetMapMarkers.value[0];
  return firstMarker ? { lat: firstMarker.lat, lng: firstMarker.lng } : target.value?.mapCenter;
});
const activeMapTargetId = computed(() => (
  selectedMapMarkerId.value ||
  target.value?.preferredMapTargetId ||
  targetMapMarkers.value[0]?.targetId ||
  ''
));

const contentToEvidenceLink = (item: NewsroomFeedItem): EvidenceLink => ({
  label: item.title,
  source: item.source,
  url: item.url,
  meta: item.meta,
  statusLabel: item.statusLabel
});

const timelineEventToItem = (item: RealEstateTimelineEvent): TimelineItem => ({
  id: item.id,
  time: timeLabel(item.occurredAt),
  title: item.title,
  detail: item.summary ?? '세부 요약 확인 필요',
  meta: timelineMeta(item)
});

const refreshTargetContent = async () => {
  if (!target.value) {
    evidenceLinks.value = [];
    evidenceLoadState.value = 'fallback';
    return;
  }

  evidenceLoadState.value = 'loading';
  try {
    const contentItems = await fetchRealEstateTargetContent(target.value.targetId, {
      feed: 'all',
      limit: 6
    });
    const mappedLinks = buildNewsroomFeedItems(contentItems).map(contentToEvidenceLink);
    evidenceLinks.value = mappedLinks;
    evidenceLoadState.value = mappedLinks.length ? 'live' : 'fallback';
  } catch {
    evidenceLinks.value = [];
    evidenceLoadState.value = 'fallback';
  }
};

const refreshTargetMapMarkers = async () => {
  if (!target.value) {
    apiMapMarkers.value = [];
    mapMarkerLoadState.value = 'fallback';
    return;
  }

  mapMarkerLoadState.value = 'loading';
  try {
    const markers = await fetchRealEstateNearbyComplexes(target.value.targetId, {
      limit: 20
    });
    apiMapMarkers.value = markers;
    mapMarkerLoadState.value = markers.length ? 'live' : 'fallback';
  } catch {
    apiMapMarkers.value = [];
    mapMarkerLoadState.value = 'fallback';
  }
};

const refreshTargetTimeline = async () => {
  if (!target.value) {
    timelineItems.value = [];
    timelineLoadState.value = 'fallback';
    return;
  }

  timelineLoadState.value = 'loading';
  try {
    const events = await fetchRealEstateTargetTimeline(target.value.targetId, {
      limit: 6
    });
    timelineItems.value = events.map(timelineEventToItem);
    timelineLoadState.value = timelineItems.value.length ? 'live' : 'fallback';
  } catch {
    timelineItems.value = [];
    timelineLoadState.value = 'fallback';
  }
};

const refreshTargetAgentEvidenceLogs = async () => {
  if (!target.value) {
    agentEvidenceLogs.value = [];
    agentEvidenceLoadState.value = 'fallback';
    return;
  }

  agentEvidenceLoadState.value = 'loading';
  try {
    const logs = await fetchRealEstateTargetEvidenceLogs(target.value.targetId, {
      limit: 3
    });
    agentEvidenceLogs.value = logs;
    agentEvidenceLoadState.value = logs.length ? 'live' : 'fallback';
  } catch {
    agentEvidenceLogs.value = [];
    agentEvidenceLoadState.value = 'fallback';
  }
};

const selectMapMarker = (marker: ComplexMapMarker) => {
  selectedMapMarkerId.value = marker.targetId;
};

onMounted(() => {
  void refreshTargetContent();
  void refreshTargetMapMarkers();
  void refreshTargetTimeline();
  void refreshTargetAgentEvidenceLogs();
});

watch(() => target.value?.targetId, () => {
  selectedMapMarkerId.value = '';
  void refreshTargetContent();
  void refreshTargetMapMarkers();
  void refreshTargetTimeline();
  void refreshTargetAgentEvidenceLogs();
});

function timeLabel(value?: string | null): string {
  if (!value) return '시각 확인 필요';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value.slice(0, 5);
  return new Intl.DateTimeFormat('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'Asia/Seoul'
  }).format(parsed);
}

function timelineMeta(item: RealEstateTimelineEvent): string {
  const eventType = item.eventType?.trim() || 'event';
  const dataStatus = item.dataStatus?.trim() || 'unknown';
  return `${eventType} · ${dataStatus}`;
}

function evidenceLogMeta(log: RealEstateEvidenceLog): string {
  const parts = [
    log.dataQuality?.trim(),
    log.tone?.trim(),
    confidenceLabel(log.confidence)
  ].filter((item): item is string => Boolean(item));
  return parts.join(' · ') || '품질 확인 필요';
}

function confidenceLabel(value?: number | null): string | null {
  if (!Number.isFinite(value)) return null;
  return `신뢰도 ${Math.round(Number(value) * 100)}%`;
}

function logVersionLabel(log: RealEstateEvidenceLog): string {
  return [log.evaluationVersion, log.promptVersion, log.modelName]
    .map((item) => item?.trim())
    .filter((item): item is string => Boolean(item))
    .join(' · ') || '평가 버전 확인 필요';
}

function caveats(log: RealEstateEvidenceLog): string[] {
  return Array.isArray(log.caveats)
    ? log.caveats.filter((item) => item.trim().length > 0)
    : [];
}

function evidenceItems(log: RealEstateEvidenceLog) {
  return Array.isArray(log.evidenceItems)
    ? log.evidenceItems.filter((item) => item.evidenceItemId && item.label)
    : [];
}
</script>

<template>
  <section v-if="target" class="surface-page region-detail-page region-detail-page">
    <section class="region-brief-panel panel" aria-label="지역 한줄 브리핑">
      <div class="region-brief-topline">
        <div>
          <strong>{{ target.name }}</strong>
          <span>{{ target.targetId }} · {{ target.region }}</span>
        </div>
        <RouterLink class="region-report-close region-report-close" to="/realestate/reactions" aria-label="지역 반응 목록으로 돌아가기">×</RouterLink>
      </div>

      <article class="region-brief-banner">
        <p class="eyebrow">지역 한줄 브리핑</p>
        <h2>{{ target.headline }}</h2>
        <span>{{ target.summary }}</span>
      </article>

      <div class="region-keyword-digest">
        <article v-for="keyword in target.keywords" :key="keyword">
          <span>핵심 키워드</span>
          <strong>{{ keyword }}</strong>
        </article>
      </div>
    </section>

    <section class="region-hero panel">
      <div class="region-identity">
        <RouterLink class="detail-link region-back-link region-back-link" to="/realestate/reactions">← 지역 반응 목록으로</RouterLink>
        <p class="eyebrow">지역 상세 리포트</p>
        <h2>{{ target.name }} <span>{{ target.targetId }} · {{ target.region }}</span></h2>
        <p>실거래, 전세, 공급, 커뮤니티 반응을 분리해서 보는 관찰형 지역 리포트입니다.</p>
      </div>

      <div class="region-metric-board">
        <article :class="target.tone">
          <span>실거래가 흐름</span>
          <strong>{{ target.indexChange }}</strong>
          <em>mock · 공개 지연 가능</em>
        </article>
        <article>
          <span>거래량</span>
          <strong>{{ target.tradeVolume }}</strong>
          <em>매매·전월세 대조 필요</em>
        </article>
        <article>
          <span>전세가율</span>
          <strong>{{ target.jeonseRatio }}</strong>
          <em>매매 전환 압력 후보</em>
        </article>
        <article>
          <span>공급 신호</span>
          <strong>{{ target.supplySignal }}</strong>
          <em>입주·미분양 확인</em>
        </article>
      </div>
    </section>

    <section class="dense-summary-strip region-density-strip" aria-label="지역 요약 지표">
      <article v-for="metric in target.metrics" :key="metric.label" :class="metric.tone">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <em>{{ metric.note }}</em>
      </article>
    </section>

    <KakaoComplexMap
      v-if="targetMapMarkers.length"
      :markers="targetMapMarkers"
      :selected-target-id="activeMapTargetId"
      :center="mapCenter"
      :level="target.mapLevel"
      :marker-source-status="mapMarkerSourceStatusLabel"
      @select="selectMapMarker"
    />

    <section class="region-layout-grid">
      <article class="panel content-feed-card surface-data-card reaction-trend-panel region-reaction-card">
        <div class="section-band-title">
          <div>
            <p class="label">community reaction</p>
            <h3>커뮤니티 반응 추이</h3>
          </div>
          <span>신뢰도 {{ target.confidence }}</span>
        </div>
        <div class="source-breakdown-list">
          <article v-for="reaction in target.reactions" :key="reaction.source">
            <strong>{{ reaction.source }}</strong>
            <span>{{ reaction.mentions }}건</span>
            <i class="reaction-track">
              <mark :style="{ width: `${reaction.positive}%` }"></mark>
              <mark class="down" :style="{ width: `${reaction.negative}%` }"></mark>
            </i>
            <em>{{ reaction.note }}</em>
          </article>
        </div>
      </article>

      <article class="panel content-feed-card surface-data-card reliability-panel region-reliability-card">
        <div class="section-band-title">
          <div>
            <p class="label">confidence</p>
            <h3>신호 신뢰도</h3>
          </div>
          <span>mock</span>
        </div>
        <div class="reliability-meter">
          <i><mark :style="{ width: `${confidenceValue}%` }"></mark></i>
          <strong>{{ target.confidence }}</strong>
          <p>표본 수, 출처 다양성, 공공데이터 지연 여부를 함께 반영한 화면용 신뢰도입니다.</p>
        </div>
      </article>
    </section>

    <section class="panel content-feed-card surface-data-card region-event-panel region-timeline-card">
      <div class="section-band-title">
        <div>
          <p class="label">event timeline</p>
          <h3>시간대별 변화</h3>
        </div>
        <span>{{ timelineSourceStatusLabel }}</span>
      </div>
      <div class="vertical-timeline">
        <article v-for="(item, index) in targetTimeline" :key="item.id ?? `${item.time}-${item.title}-${index}`">
          <time>{{ item.time }}</time>
          <strong>{{ item.title }}</strong>
          <p>{{ item.detail }}</p>
          <span v-if="item.meta">{{ item.meta }}</span>
        </article>
      </div>
    </section>

    <section class="panel content-feed-card surface-data-card decision-log-panel region-agent-evidence-card">
      <div class="section-band-title">
        <div>
          <p class="label">agent evidence</p>
          <h3>AI 근거 로그</h3>
        </div>
        <span>{{ agentEvidenceStatusLabel }}</span>
      </div>
      <div v-if="agentEvidenceLogs.length" class="decision-log-list agent-evidence-list">
        <article v-for="log in agentEvidenceLogs" :key="log.evidenceLogId">
          <time>{{ timeLabel(log.evaluatedAt) }}</time>
          <div>
            <strong>{{ log.summary }}</strong>
            <p v-if="log.subtitle">{{ log.subtitle }}</p>
            <div class="agent-evidence-meta-strip">
              <span>{{ evidenceLogMeta(log) }}</span>
              <code>{{ logVersionLabel(log) }}</code>
            </div>
            <div v-if="caveats(log).length" class="agent-evidence-caveats" aria-label="근거 로그 주의점">
              <span v-for="caveat in caveats(log)" :key="`${log.evidenceLogId}-${caveat}`">{{ caveat }}</span>
            </div>
            <div v-if="evidenceItems(log).length" class="agent-evidence-items" aria-label="근거 항목">
              <span v-for="item in evidenceItems(log)" :key="item.evidenceItemId">
                <b>{{ item.label }}</b>
                <em>{{ item.valueText || item.evidenceType || '값 확인 필요' }}</em>
              </span>
            </div>
            <p v-if="log.skipReason" class="agent-evidence-skip">스킵 사유: {{ log.skipReason }}</p>
          </div>
        </article>
      </div>
      <p v-else class="agent-evidence-empty">아직 저장된 AI 근거 로그가 없습니다. 배치가 평가를 생성하면 이 영역에 평가 버전, caveat, 근거 항목이 표시됩니다.</p>
    </section>

    <section class="panel content-feed-card surface-data-card evidence-panel region-evidence-card">
      <div class="section-band-title">
        <div>
          <p class="label">evidence</p>
          <h3>근거 링크 후보</h3>
        </div>
        <span>{{ evidenceStatusLabel }}</span>
      </div>
      <div class="evidence-list">
        <a v-for="item in targetEvidence" :key="item.label" :href="item.url" target="_blank" rel="noreferrer noopener">
          <strong>{{ item.label }}</strong>
          <span>{{ item.source }}</span>
          <em v-if="item.meta">{{ item.meta }}</em>
        </a>
      </div>
    </section>
  </section>

  <section v-else class="surface-page region-detail-page unsupported-region-state" aria-label="지원 준비 중인 지역">
    <section class="region-brief-panel panel">
      <div class="region-brief-topline">
        <div>
          <strong>지원 준비 중인 지역</strong>
          <span>{{ routeTargetId || 'UNKNOWN' }}</span>
        </div>
        <RouterLink class="region-report-close region-report-close" to="/realestate/reactions" aria-label="지역 반응 목록으로 돌아가기">×</RouterLink>
      </div>

      <article class="region-brief-banner">
        <p class="eyebrow">지역 상세 리포트</p>
        <h2>아직 상세 리포트가 연결되지 않았습니다</h2>
        <span>선택한 지역/단지는 순위와 반응 화면에서 관찰 후보로 표시되지만, 상세 mock 데이터는 아직 준비되지 않았습니다. 잘못된 지역 리포트를 대신 보여주지 않고 지원 준비 상태로 표시합니다.</span>
      </article>
    </section>

    <section class="region-hero panel">
      <div class="region-identity">
        <RouterLink class="detail-link region-back-link region-back-link" to="/realestate/reactions">← 지역 반응 목록으로</RouterLink>
        <p class="eyebrow">unsupported target</p>
        <h2>{{ routeTargetId || 'UNKNOWN' }} <span>상세 데이터 미연결</span></h2>
        <p>해당 대상의 상세 지표, 커뮤니티 반응, 근거 링크가 준비되면 이 페이지에서 실제 리포트로 전환됩니다.</p>
      </div>

      <div class="region-metric-board">
        <article>
          <span>상태</span>
          <strong>준비 중</strong>
          <em>잘못된 fallback 차단</em>
        </article>
        <article>
          <span>요청 대상 ID</span>
          <strong>{{ routeTargetId || 'UNKNOWN' }}</strong>
          <em>지역/단지 alias 확인 필요</em>
        </article>
        <article>
          <span>상세 데이터</span>
          <strong>미연결</strong>
          <em>mock 확장 후보</em>
        </article>
        <article>
          <span>다음 경로</span>
          <strong>목록 복귀</strong>
          <em>반응 화면에서 재확인</em>
        </article>
      </div>
    </section>
  </section>
</template>
