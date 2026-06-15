<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  buildRegionRankingRows,
  fetchRealEstateReactionRanking
} from '../lib/realestate-reactions';

type MovementTone = 'up' | 'down';
type ReactionTone = 'positive' | 'negative' | 'watch' | 'neutral';
type RegionReactionView = 'overview' | 'ranking' | 'signals' | 'agents';
type RegionScope = '전체' | '서울' | '경기' | '대전' | '인천';

type RegionRankingRow = {
  rank: number;
  name: string;
  targetId: string;
  market: string;
  price: string;
  change: string;
  mentions: string;
  mentionDelta: string;
  positive: number;
  negative: number;
  event: string;
  freshness: string;
  tone: MovementTone;
};

type SignalTile = {
  label: string;
  target: string;
  targetId: string;
  metric: string;
  tone: ReactionTone;
  summary: string;
  reasons: string[];
  pulse: number;
  community: string;
};

type AgentLog = {
  time: string;
  strategy: '지표 동행 관찰' | '커뮤니티 선행 관찰';
  target: string;
  targetId: string;
  state: string;
  input: string;
  reason: string;
  key: string;
};

const route = useRoute();
const activeRegionReactionView = computed<RegionReactionView>(() => {
  const rawView = route.query.view;
  const view = Array.isArray(rawView) ? rawView[0] : rawView;

  if (view === 'ranking' || view === 'signals' || view === 'agents') {
    return view;
  }

  return 'overview';
});

const reactionViewTabs = [
  { label: '종합', view: 'overview', to: { path: '/realestate/reactions' } },
  { label: '순위', view: 'ranking', to: { path: '/realestate/reactions', query: { view: 'ranking' } } },
  { label: '반응', view: 'signals', to: { path: '/realestate/reactions', query: { view: 'signals' } } },
  { label: '근거 로그', view: 'agents', to: { path: '/realestate/reactions', query: { view: 'agents' } } }
] satisfies {
  label: string;
  view: RegionReactionView;
  to: { path: string; query?: Record<string, string> };
}[];

const isSectionVisible = (section: Exclude<RegionReactionView, 'overview'>) =>
  activeRegionReactionView.value === 'overview' || activeRegionReactionView.value === section;

const regionRows: RegionRankingRow[] = [
  { rank: 1, name: '마포구 아파트', targetId: 'region-seoul-mapo', market: '서울', price: '14.5억', change: '+0.55%', mentions: '128건', mentionDelta: '+42%', positive: 49, negative: 33, event: '전세·공덕·학군', freshness: '실거래 지연', tone: 'up' },
  { rank: 2, name: '동탄역권', targetId: 'living-area-gyeonggi-dongtan-station', market: '경기', price: '9.8억', change: '+0.31%', mentions: '74건', mentionDelta: '+19%', positive: 44, negative: 39, event: 'GTX·입주', freshness: '공공데이터 stale', tone: 'up' },
  { rank: 3, name: '성수동 생활권', targetId: 'living-area-seoul-seongsu', market: '서울', price: '18.2억', change: '+0.66%', mentions: '41건', mentionDelta: '+86%', positive: 56, negative: 25, event: '상권·개발', freshness: 'mock', tone: 'up' },
  { rank: 4, name: '잠실동 단지군', targetId: 'living-area-seoul-jamsil', market: '서울', price: '22.5억', change: '-0.22%', mentions: '43건', mentionDelta: '+54%', positive: 47, negative: 29, event: '토허제·재건축', freshness: '정책 이슈', tone: 'down' },
  { rank: 5, name: '분당·판교', targetId: 'living-area-gyeonggi-bundang-pangyo', market: '경기', price: '17.6억', change: '+0.51%', mentions: '66건', mentionDelta: '+30%', positive: 58, negative: 24, event: '일자리·학군', freshness: 'mock', tone: 'up' },
  { rank: 6, name: '송도국제도시', targetId: 'living-area-incheon-songdo', market: '인천', price: '8.4억', change: '-0.18%', mentions: '38건', mentionDelta: '+21%', positive: 42, negative: 36, event: '공급·국제학교', freshness: 'stale', tone: 'down' },
  { rank: 7, name: '대전 유성구', targetId: 'region-daejeon-yuseong', market: '대전', price: '7.6억', change: '+0.24%', mentions: '31건', mentionDelta: '+18%', positive: 45, negative: 31, event: '연구단지·전세', freshness: '수집 전', tone: 'up' },
  { rank: 8, name: '파주 운정', targetId: 'living-area-gyeonggi-paju-unjeong', market: '경기', price: '6.7억', change: '-0.12%', mentions: '29건', mentionDelta: '+15%', positive: 39, negative: 43, event: 'GTX·입주물량', freshness: 'insufficient', tone: 'down' },
  { rank: 9, name: '세종 새롬동', targetId: 'living-area-sejong-saerom', market: '세종', price: '7.1억', change: '+0.08%', mentions: '24건', mentionDelta: '+11%', positive: 41, negative: 34, event: '정책·공급', freshness: '수집 전', tone: 'up' },
  { rank: 10, name: '부산 해운대', targetId: 'region-busan-haeundae', market: '부산', price: '10.4억', change: '-0.05%', mentions: '22건', mentionDelta: '+9%', positive: 38, negative: 37, event: '관광·전세', freshness: 'insufficient', tone: 'down' }
];

const complexRows: RegionRankingRow[] = [
  { rank: 1, name: '래미안 원베일리', targetId: 'complex-raemian-onebailey', market: '반포', price: '41.0억', change: '+0.28%', mentions: '58건', mentionDelta: '+36%', positive: 52, negative: 27, event: '신고가·전세', freshness: 'mock', tone: 'up' },
  { rank: 2, name: '헬리오시티', targetId: 'complex-helio-city', market: '송파', price: '20.7억', change: '-0.08%', mentions: '49건', mentionDelta: '+24%', positive: 41, negative: 38, event: '전세 매물', freshness: 'mock', tone: 'down' },
  { rank: 3, name: '마포래미안푸르지오', targetId: 'complex-mapo-raemian-prugio', market: '마포', price: '15.3억', change: '+0.21%', mentions: '44건', mentionDelta: '+28%', positive: 48, negative: 31, event: '학군·역세권', freshness: '실거래 지연', tone: 'up' },
  { rank: 4, name: '판교푸르지오그랑블', targetId: 'complex-pangyo-prugio-grandble', market: '판교', price: '22.4억', change: '+0.34%', mentions: '37건', mentionDelta: '+18%', positive: 61, negative: 20, event: '일자리·학군', freshness: 'mock', tone: 'up' },
  { rank: 5, name: '송도더샵센트럴', targetId: 'complex-songdo-the-sharp-central', market: '송도', price: '8.9억', change: '-0.16%', mentions: '32건', mentionDelta: '+17%', positive: 39, negative: 40, event: '공급 부담', freshness: 'stale', tone: 'down' },
  { rank: 6, name: '동탄역 롯데캐슬', targetId: 'complex-dongtan-lotte-castle', market: '동탄', price: '12.2억', change: '+0.19%', mentions: '35건', mentionDelta: '+22%', positive: 46, negative: 35, event: 'GTX·입주', freshness: 'mock', tone: 'up' },
  { rank: 7, name: '도안 우미린', targetId: 'complex-daejeon-doan-umirin', market: '대전', price: '6.9억', change: '+0.17%', mentions: '27건', mentionDelta: '+14%', positive: 43, negative: 32, event: '학군·신축', freshness: '수집 전', tone: 'up' },
  { rank: 8, name: '운정 아이파크', targetId: 'complex-paju-unjeong-ipark', market: '파주', price: '6.4억', change: '-0.11%', mentions: '25건', mentionDelta: '+12%', positive: 37, negative: 45, event: '입주·교통', freshness: 'insufficient', tone: 'down' },
  { rank: 9, name: '센텀 리더스마크', targetId: 'complex-busan-centum-leadersmark', market: '부산', price: '9.8억', change: '+0.06%', mentions: '21건', mentionDelta: '+10%', positive: 40, negative: 35, event: '상권·전세', freshness: '수집 전', tone: 'up' },
  { rank: 10, name: '새롬 더샵힐스', targetId: 'complex-sejong-saerom-thesharp', market: '세종', price: '7.2억', change: '-0.04%', mentions: '19건', mentionDelta: '+8%', positive: 36, negative: 39, event: '공급·정책', freshness: 'insufficient', tone: 'down' }
];

const rankingLoadState = ref<'loading' | 'live' | 'empty' | 'fallback'>('loading');
const liveRegionRows = ref<RegionRankingRow[]>([]);
const liveComplexRows = ref<RegionRankingRow[]>([]);
const selectedRegionScope = ref<RegionScope>('전체');

const regionScopeOptions = [
  { value: '전체', label: '전체 TOP10' },
  { value: '서울', label: '서울 TOP10' },
  { value: '경기', label: '경기 TOP10' },
  { value: '대전', label: '대전 TOP10' },
  { value: '인천', label: '인천 TOP10' }
] satisfies { value: RegionScope; label: string }[];

const regionScopeParentTargetIds: Partial<Record<RegionScope, string>> = {
  서울: 'region-seoul',
  경기: 'region-gyeonggi',
  대전: 'region-daejeon',
  인천: 'region-incheon'
};

const scopeTitlePrefix = computed(() => (selectedRegionScope.value === '전체' ? '' : `${selectedRegionScope.value} `));
const selectedParentTargetId = computed(() => regionScopeParentTargetIds[selectedRegionScope.value]);

const rowsForSelectedScope = (rows: RegionRankingRow[]) => {
  if (selectedRegionScope.value === '전체') return rows;
  return rows.filter((row) => inferRegionScope(row) === selectedRegionScope.value);
};

const scopedRegionRows = computed(() => rowsForSelectedScope(liveRegionRows.value));
const scopedComplexRows = computed(() => rowsForSelectedScope(liveComplexRows.value));

const rankingGroups = computed(() => [
  { id: 'regions', title: `${scopeTitlePrefix.value}지역 언급량 TOP 10`, caption: '시도·생활권 기준', rows: scopedRegionRows.value },
  { id: 'complexes', title: `${scopeTitlePrefix.value}단지군 관심 TOP 10`, caption: '아파트·생활권 후보', rows: scopedComplexRows.value }
]);

const refreshReactionRankings = async () => {
  try {
    const parentTargetId = selectedParentTargetId.value;
    const [regionRanking, complexRanking] = await Promise.all([
      fetchRealEstateReactionRanking({ type: 'region', windowMinutes: 1440, limit: 10, parentTargetId }),
      fetchRealEstateReactionRanking({ type: 'complex', windowMinutes: 1440, limit: 10, parentTargetId })
    ]);
    const hasRegionItems = regionRanking.items.length > 0;
    const hasComplexItems = complexRanking.items.length > 0;
    liveRegionRows.value = hasRegionItems ? buildRegionRankingRows(regionRanking, regionRows) : [];
    liveComplexRows.value = hasComplexItems ? buildRegionRankingRows(complexRanking, complexRows) : [];
    rankingLoadState.value = hasRegionItems || hasComplexItems ? 'live' : 'empty';
  } catch {
    liveRegionRows.value = regionRows;
    liveComplexRows.value = complexRows;
    rankingLoadState.value = 'fallback';
  }
};

onMounted(() => {
  void refreshReactionRankings();
});

watch(selectedRegionScope, () => {
  void refreshReactionRankings();
});

const filters = ['언급 증가', '전세 우려', '실거래 지연', '공급 부담', '정책 민감', 'stale 제외'];

function inferRegionScope(row: RegionRankingRow): RegionScope | '기타' {
  const key = `${row.targetId} ${row.name} ${row.market}`;
  if (/seoul|mapo|jamsil|songpa|banpo|helio|서울|마포|잠실|송파|반포|성수/.test(key)) return '서울';
  if (/gyeonggi|dongtan|bundang|pangyo|paju|경기|동탄|분당|판교|파주|운정/.test(key)) return '경기';
  if (/daejeon|대전|도안|유성/.test(key)) return '대전';
  if (/incheon|songdo|인천|송도/.test(key)) return '인천';
  return '기타';
}

const rankingSourceMeta = computed(() => {
  if (rankingLoadState.value === 'fallback') return 'fixture fallback';
  if (rankingLoadState.value === 'loading') return 'API 조회 중';
  if (rankingLoadState.value === 'empty') return '수집 전/insufficient';
  return 'API ranking';
});

const rowCountMeta = (count: number) => {
  if (count > 0) return rankingSourceMeta.value;
  if (rankingLoadState.value === 'loading') return '조회 중';
  return '수집 전';
};

const rankSummary = computed(() => [
  { label: '정렬 기준', value: '언급량', meta: rankingSourceMeta.value },
  { label: '지역 표시', value: `${scopedRegionRows.value.length}곳`, meta: rowCountMeta(scopedRegionRows.value.length) },
  { label: '단지 표시', value: `${scopedComplexRows.value.length}곳`, meta: rowCountMeta(scopedComplexRows.value.length) },
  { label: '보조 지표', value: '수급·전세', meta: '기대/우려 비율' }
]);

const hotThemes = [
  { theme: '전세 매물', count: 14, heat: 88 },
  { theme: 'GTX·교통', count: 9, heat: 76 },
  { theme: '재건축', count: 7, heat: 69 },
  { theme: '공급 부담', count: 6, heat: 63 }
];

const signalTiles: SignalTile[] = [
  {
    label: '언급 급증',
    target: '성수동 생활권',
    targetId: 'living-area-seoul-seongsu',
    metric: '+86%',
    tone: 'positive',
    summary: '상권, 개발, 임대료 키워드가 영상과 블로그에서 동시에 늘었습니다.',
    reasons: ['지역 블로그 상위 노출', '댓글 속도 1.8배', '상권 키워드 확산'],
    pulse: 88,
    community: '지역 블로그'
  },
  {
    label: '기대 우세',
    target: '분당·판교',
    targetId: 'living-area-gyeonggi-bundang-pangyo',
    metric: '기대 58',
    tone: 'positive',
    summary: '일자리와 재건축 기대 키워드가 짧은 시간에 올라왔습니다.',
    reasons: ['직장인 커뮤니티 확산', '재건축 별칭 언급', '기대 58 / 우려 24'],
    pulse: 72,
    community: '블라인드'
  },
  {
    label: '우려 증가',
    target: '송도국제도시',
    targetId: 'living-area-incheon-songdo',
    metric: '우려 36',
    tone: 'negative',
    summary: '공급 부담, 미분양, 전세 매물 키워드가 반복됩니다.',
    reasons: ['네이버 카페 공급 논쟁', '공공데이터 stale', '출처 편중 54%'],
    pulse: 64,
    community: '네이버 카페'
  },
  {
    label: '정책 민감',
    target: '잠실동 단지군',
    targetId: 'living-area-seoul-jamsil',
    metric: '+54%',
    tone: 'negative',
    summary: '토허제, 재건축, 대출 규제 키워드가 동시에 올라와 관찰이 필요합니다.',
    reasons: ['정책 댓글 급증', '재건축 별칭 반복', '규제 관망 확산'],
    pulse: 68,
    community: '지역 카페'
  }
];

const visibleSignalTiles = computed<SignalTile[]>(() => {
  if (rankingLoadState.value === 'fallback') {
    return signalTiles;
  }

  return liveRegionRows.value.slice(0, 4).map(signalTileFromRankingRow);
});

function signalTileFromRankingRow(row: RegionRankingRow, index: number): SignalTile {
  return {
    label: signalTileLabel(row, index),
    target: row.name,
    targetId: row.targetId,
    metric: row.mentionDelta,
    tone: row.negative > row.positive ? 'negative' : row.tone === 'down' ? 'negative' : 'positive',
    summary: `${row.mentions} 언급, ${row.event} 쟁점이 관찰됩니다.`,
    reasons: [
      row.freshness,
      `기대 ${row.positive} / 우려 ${row.negative}`,
      row.market
    ],
    pulse: signalPulse(row),
    community: 'API ranking'
  };
}

function signalTileLabel(row: RegionRankingRow, index: number): SignalTile['label'] {
  if (index === 0) return '언급 급증';
  if (row.negative > row.positive) return '우려 증가';
  if (row.event.includes('정책')) return '정책 민감';
  if (row.positive > row.negative) return '기대 우세';
  return '반응 관찰';
}

function signalPulse(row: RegionRankingRow): number {
  const mentionCount = Number(row.mentions.replace(/[^\d]/g, ''));
  if (!Number.isFinite(mentionCount) || mentionCount <= 0) return 35;
  return Math.max(35, Math.min(100, mentionCount * 3));
}

const agentLogs: AgentLog[] = [
  {
    time: '10:12',
    strategy: '지표 동행 관찰',
    target: '마포구 아파트',
    targetId: 'region-seoul-mapo',
    state: '알림 후보',
    input: '언급 +42% · 기대 49 · 전세가율 상승',
    reason: '전세 체감과 가격지표가 같은 방향',
    key: 'region-follow-seoul-mapo-1012'
  },
  {
    time: '10:04',
    strategy: '커뮤니티 선행 관찰',
    target: '송도국제도시',
    targetId: 'living-area-incheon-songdo',
    state: '관찰만',
    input: '우려 36 · 공급 키워드 · 실거래 stale',
    reason: '공급 부담 반응은 강하지만 가격 지표가 늦음',
    key: 'community-lead-songdo-1004'
  },
  {
    time: '09:51',
    strategy: '지표 동행 관찰',
    target: '성수동 생활권',
    targetId: 'living-area-seoul-seongsu',
    state: '관찰 유지',
    input: '언급 +86% · 상권 키워드 · 출처 4곳',
    reason: '블로그와 영상 제목이 동시에 증가',
    key: 'region-follow-seongsu-0951'
  },
  {
    time: '09:37',
    strategy: '커뮤니티 선행 관찰',
    target: '동탄역권',
    targetId: 'living-area-gyeonggi-dongtan-station',
    state: '확인 필요',
    input: 'GTX 관심 +24% · 입주 우려 · 전세수급 상승',
    reason: '기대와 우려가 상쇄되어 공공데이터 대조 필요',
    key: 'community-lead-dongtan-0937'
  }
];

const strategyRules = [
  { name: '지표 동행 관찰', version: 'realestate-follow-v1', rule: '언급 증가, 수급지수, 가격지표가 같은 방향일 때 알림 후보로 둡니다.', keys: 9 },
  { name: '커뮤니티 선행 관찰', version: 'community-lead-v1', rule: '공식 지표보다 커뮤니티 반응이 먼저 움직이면 원문 확인 후보로 둡니다.', keys: 6 }
];
</script>

<template>
  <section class="surface-page region-reaction-page region-reactions-page region-reactions-board-page reaction-dashboard-page">
    <section class="region-reaction-hero reaction-hero-panel" aria-labelledby="region-reaction-title">
      <div class="reaction-hero-copy">
        <p class="label">region reaction</p>
        <h2 id="region-reaction-title">지역 반응</h2>
        <span>지역·단지 순위, 급증 신호, 모의 에이전트 근거 로그를 한 화면에서 봅니다.</span>
      </div>
      <nav class="reaction-view-tabs compact" aria-label="지역 반응 하위 화면">
        <RouterLink
          v-for="tab in reactionViewTabs"
          :key="tab.view"
          :class="{ active: activeRegionReactionView === tab.view }"
          :to="tab.to"
        >
          {{ tab.label }}
        </RouterLink>
      </nav>
    </section>

    <section
      v-if="activeRegionReactionView !== 'agents'"
      class="reaction-signal-board region-signal-overview-board"
      aria-label="커뮤니티 언급 급증 지역"
    >
      <div class="section-band-title full">
        <div>
          <p class="label">community pulse</p>
          <h3>커뮤니티 언급 급증 지역</h3>
        </div>
        <span>{{ rankingLoadState === 'fallback' ? '언급 급증, 기대 우세, 우려 증가, 정책 민감을 한 줄로 통합' : 'TOP10 API 기준 언급 증가와 기대·우려를 한 줄로 통합' }}</span>
      </div>
      <p v-if="rankingLoadState === 'loading'" class="reaction-signal-empty">
        지역 급증 신호를 불러오는 중입니다.
      </p>
      <p v-else-if="!visibleSignalTiles.length" class="reaction-signal-empty">
        수집된 지역 급증 신호가 아직 없습니다. 수집 전/insufficient 상태로 표시합니다.
      </p>
      <RouterLink
        v-for="tile in visibleSignalTiles"
        :key="tile.label"
        :class="['reaction-signal-tile', tile.tone]"
        :to="`/realestate/targets/${tile.targetId}`"
      >
        <div class="signal-tile-top">
          <span>{{ tile.label }}</span>
          <em>{{ tile.community }}</em>
        </div>
        <strong>{{ tile.target }}</strong>
        <b>{{ tile.metric }}</b>
        <p>{{ tile.summary }}</p>
        <div class="signal-reason-row">
          <small v-for="reason in tile.reasons" :key="reason">{{ reason }}</small>
        </div>
        <i class="signal-pulse-track">
          <mark :style="{ width: `${tile.pulse}%` }"></mark>
        </i>
      </RouterLink>
    </section>

    <template v-if="isSectionVisible('ranking')">

      <div class="region-filter-strip region-scope-filter" aria-label="시도별 TOP10 필터">
        <button
          v-for="scope in regionScopeOptions"
          :key="scope.value"
          type="button"
          :class="{ active: selectedRegionScope === scope.value }"
          @click="selectedRegionScope = scope.value"
        >
          {{ scope.label }}
        </button>
      </div>

      <div class="region-filter-strip" aria-label="지역 필터">
        <button v-for="filter in filters" :key="filter" type="button">{{ filter }}</button>
      </div>

      <section class="rank-summary-strip" aria-label="랭킹 요약">
        <article v-for="item in rankSummary" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <em>{{ item.meta }}</em>
        </article>
      </section>

      <section class="region-ranking-grid" aria-label="지역과 단지 관심 순위">
        <div
          v-for="group in rankingGroups"
          :key="group.id"
          class="region-rank-panel"
          :aria-label="group.title"
        >
          <div class="section-band-title">
            <div>
              <p class="label">{{ group.caption }}</p>
              <h3>{{ group.title }}</h3>
            </div>
            <span>{{ rankingLoadState === 'fallback' ? '언급량순 mock' : group.rows.length ? 'API 반영' : '수집 전' }}</span>
          </div>

          <div class="region-ranking-head">
            <span>순위</span>
            <span>지역/단지</span>
            <span>언급량</span>
            <span>반응</span>
            <span>쟁점</span>
          </div>

          <p v-if="rankingLoadState === 'loading'" class="region-ranking-empty">
            TOP10 데이터를 불러오는 중입니다.
          </p>
          <p v-else-if="!group.rows.length" class="region-ranking-empty">
            수집된 TOP10 데이터가 아직 없습니다. 수집 전/insufficient 상태로 표시합니다.
          </p>

          <RouterLink
            v-for="row in group.rows"
            :key="row.targetId"
            class="region-ranking-row"
            :to="`/realestate/targets/${row.targetId}`"
          >
            <b>{{ row.rank }}</b>
            <div>
              <strong>{{ row.name }}</strong>
              <small>{{ row.targetId }} · {{ row.market }} · {{ row.price }} <em :class="row.tone">{{ row.change }}</em></small>
            </div>
            <div>
              <strong>{{ row.mentions }}</strong>
              <em>{{ row.mentionDelta }}</em>
            </div>
            <div class="region-mini-ratio">
              <span>{{ row.positive }}</span>
              <i>
                <mark :style="{ width: `${row.positive}%` }"></mark>
                <mark class="down" :style="{ width: `${row.negative}%` }"></mark>
              </i>
              <span>{{ row.negative }}</span>
            </div>
            <div>
              <span>{{ row.event }}</span>
              <small>{{ row.freshness }}</small>
            </div>
          </RouterLink>
        </div>
      </section>

      <aside class="region-side-console region-ranking-console" aria-label="랭킹 보조 지표">
        <section>
          <p class="label">theme heat</p>
          <h3>급증 쟁점</h3>
          <article v-for="theme in hotThemes" :key="theme.theme">
            <strong>{{ theme.theme }}</strong>
            <span>{{ theme.count }}곳</span>
            <i><mark :style="{ width: `${theme.heat}%` }"></mark></i>
          </article>
        </section>
        <section>
          <p class="label">data clock</p>
          <h3>데이터 기준</h3>
          <div class="clock-grid">
            <span>수집</span><strong>10:05</strong>
            <span>실거래</span><strong>공개 지연</strong>
            <span>언급량</span><strong>mock</strong>
            <span>상태</span><strong>demo</strong>
          </div>
        </section>
      </aside>
    </template>

    <section
      v-if="isSectionVisible('agents')"
      id="agent-analysis-log"
      class="reaction-agent-section compact-ledger"
      aria-labelledby="reaction-agent-title"
    >
      <div class="section-band-title">
        <div>
          <p class="label">agent analysis</p>
          <h3 id="reaction-agent-title">모의 에이전트 판단 기록</h3>
        </div>
        <span>최근 판단 로그 · 반응 지표 기반 · 부동산 자문 아님</span>
      </div>

      <div class="agent-log-board">
        <div class="agent-log-head">
          <span>시간</span>
          <span>지역/단지</span>
          <span>전략</span>
          <span>상태</span>
          <span>판단 입력값</span>
          <span>판단 key</span>
        </div>
        <RouterLink
          v-for="log in agentLogs"
          :key="log.key"
          class="agent-log-row"
          :to="`/realestate/targets/${log.targetId}`"
        >
          <time>{{ log.time }}</time>
          <strong>{{ log.target }}</strong>
          <span>{{ log.strategy }}</span>
          <em>{{ log.state }}</em>
          <p>{{ log.input }} · {{ log.reason }}</p>
          <code>{{ log.key }}</code>
        </RouterLink>
      </div>

      <div class="strategy-key-strip" aria-label="전략 버전과 판단 key 기준">
        <article v-for="rule in strategyRules" :key="`${rule.version}-strip`">
          <strong>전략 버전과 판단 key 기준</strong>
          <span>{{ rule.version }} · {{ rule.name }}</span>
          <em>{{ rule.rule }}</em>
        </article>
      </div>
    </section>
  </section>
</template>
