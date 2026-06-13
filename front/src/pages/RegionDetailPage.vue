<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import {
  buildNewsroomFeedItems,
  fetchRealEstateTargetContent,
  type NewsroomFeedItem
} from '../lib/realestate-content';

type DetailTone = 'up' | 'down' | 'flat';

type RealEstateTarget = {
  targetId: string;
  apiTargetId: string;
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
  timeline: { time: string; title: string; detail: string }[];
  evidence: EvidenceLink[];
};

type EvidenceLink = {
  label: string;
  source: string;
  url: string;
  meta?: string;
  statusLabel?: string;
};

const route = useRoute();

const targets: RealEstateTarget[] = [
  {
    targetId: 'SEOUL-MAPO',
    apiTargetId: 'region-seoul-mapo',
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
    ]
  },
  {
    targetId: 'DONGTAN-STATION',
    apiTargetId: 'region-gyeonggi-dongtan-station',
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
    ]
  }
];

const routeTargetId = computed(() => String(route.params.targetId ?? '').toUpperCase());
const target = computed(() => targets.find((item) => item.targetId.toUpperCase() === routeTargetId.value));
const confidenceValue = computed(() => (target.value ? Number.parseInt(target.value.confidence, 10) : 0));
const evidenceLinks = ref<EvidenceLink[]>([]);
const evidenceLoadState = ref<'loading' | 'live' | 'fallback'>('loading');
const targetEvidence = computed(() => (
  evidenceLoadState.value === 'live' ? evidenceLinks.value : target.value?.evidence ?? []
));
const evidenceStatusLabel = computed(() => {
  if (evidenceLoadState.value === 'live') return 'content API 반영';
  if (evidenceLoadState.value === 'loading') return 'content API 확인 중';
  return '원문 확인 필요';
});

const contentToEvidenceLink = (item: NewsroomFeedItem): EvidenceLink => ({
  label: item.title,
  source: item.source,
  url: item.url,
  meta: item.meta,
  statusLabel: item.statusLabel
});

const refreshTargetContent = async () => {
  if (!target.value) {
    evidenceLinks.value = [];
    evidenceLoadState.value = 'fallback';
    return;
  }

  evidenceLoadState.value = 'loading';
  try {
    const contentItems = await fetchRealEstateTargetContent(target.value.apiTargetId, {
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

onMounted(() => {
  void refreshTargetContent();
});

watch(() => target.value?.apiTargetId, () => {
  void refreshTargetContent();
});
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
        <span>실시간 수집 전 mock</span>
      </div>
      <div class="vertical-timeline">
        <article v-for="item in target.timeline" :key="`${item.time}-${item.title}`">
          <time>{{ item.time }}</time>
          <strong>{{ item.title }}</strong>
          <p>{{ item.detail }}</p>
        </article>
      </div>
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
