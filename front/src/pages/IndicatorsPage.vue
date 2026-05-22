<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

type Tone = 'up' | 'down' | 'neutral';

type MarketGroup = {
  id: string;
  label: string;
  title: string;
  headline: string;
  change: string;
  tone: Tone;
  summary: string;
  chips: string[];
  metrics: { name: string; value: string; tone: Tone }[];
};

type SectorTile = {
  name: string;
  direction: 'up' | 'down';
  change: string;
  heat: number;
  keyword: string;
};

const route = useRoute();

const marketGroups: MarketGroup[] = [
  {
    id: 'domestic',
    label: 'KR market',
    title: '국내주식',
    headline: '반도체가 지수를 끌고 2차전지는 식는 중',
    change: '+0.44%',
    tone: 'up',
    summary: 'KOSPI는 강보합, KOSDAQ은 약세입니다. 커뮤니티는 반도체와 장비주에 몰려 있습니다.',
    chips: ['KOSPI 2,742.18', 'KOSDAQ 874.32', '반도체 언급 +28%'],
    metrics: [
      { name: 'KOSPI', value: '2,742.18', tone: 'up' },
      { name: 'KOSDAQ', value: '874.32', tone: 'down' },
      { name: 'KRX 반도체', value: '+1.4%', tone: 'up' }
    ]
  },
  {
    id: 'us',
    label: 'US market',
    title: '미국주식',
    headline: 'AI 대형주는 강한데 소비주는 눌림',
    change: '+0.72%',
    tone: 'up',
    summary: 'NASDAQ과 SOX가 강하고 VIX는 낮습니다. 미국주식 게시글은 AI, GPU, 레버리지 ETF에 집중됩니다.',
    chips: ['NASDAQ 16,340.87', 'SOX +1.12%', 'VIX 14.8'],
    metrics: [
      { name: 'NASDAQ', value: '16,340.87', tone: 'up' },
      { name: 'SOX', value: '5,218.4', tone: 'up' },
      { name: 'VIX', value: '14.8', tone: 'down' }
    ]
  },
  {
    id: 'bonds',
    label: 'rates',
    title: '채권',
    headline: '금리 민감주는 눈치 보는 구간',
    change: '+0.03p',
    tone: 'down',
    summary: '미국 10년물은 소폭 상승했습니다. 성장주와 리츠 관련 반응은 조심스럽게 바뀌었습니다.',
    chips: ['미국 10Y 4.41%', '한국 3Y 3.38%', 'FOMC 대기'],
    metrics: [
      { name: '미국 10Y', value: '4.41%', tone: 'down' },
      { name: '한국 3Y', value: '3.38%', tone: 'neutral' },
      { name: '금리 반응', value: '+9%', tone: 'up' }
    ]
  },
  {
    id: 'commodities',
    label: 'commodity',
    title: '원자재',
    headline: '유가는 오르고 금은 안전자산 쪽으로 유지',
    change: '+0.60%',
    tone: 'up',
    summary: 'WTI와 금이 모두 소폭 상승했습니다. 정유, 운송, 안전자산 키워드가 분리되어 움직입니다.',
    chips: ['WTI 78.4', '금 2,380', '정유 관심 +4%'],
    metrics: [
      { name: 'WTI', value: '78.4', tone: 'up' },
      { name: '금', value: '2,380', tone: 'up' },
      { name: '구리', value: '+0.3%', tone: 'neutral' }
    ]
  }
];

const detailRows: Record<string, { label: string; value: string; note: string; tone: Tone }[]> = {
  domestic: [
    { label: '상승 섹터 수', value: '4 / 6', note: '반도체, 로봇, 금융 우세', tone: 'up' },
    { label: '커뮤니티 괴리', value: 'NAVER', note: '가격 상승인데 부정 반응 증가', tone: 'down' },
    { label: '일정 민감도', value: '실적 발표', note: '반도체 장비주 댓글 속도 증가', tone: 'up' },
    { label: '시장 폭', value: '58%', note: '상승 종목이 우세하지만 대형주 편중', tone: 'neutral' }
  ],
  us: [
    { label: '상승 섹터 수', value: '3 / 6', note: 'AI와 에너지 우세', tone: 'up' },
    { label: '커뮤니티 괴리', value: 'SOXS', note: 'ETF 상승인데 부정 언급 우세', tone: 'down' },
    { label: '일정 민감도', value: 'PCE', note: '금리 민감 글 증가', tone: 'neutral' },
    { label: '시장 폭', value: '51%', note: 'AI 대형주 중심으로 폭이 좁음', tone: 'neutral' }
  ],
  bonds: [
    { label: '미국 10Y', value: '4.41%', note: '성장주 반응을 누르는 구간', tone: 'down' },
    { label: '한국 3Y', value: '3.38%', note: '금융주 배당 글과 연결', tone: 'neutral' },
    { label: '반응 키워드', value: 'FOMC', note: '리츠, 성장주, 환율 글에서 반복', tone: 'up' },
    { label: '환율 민감도', value: '+12%', note: '수출주 글에서 원달러 키워드 증가', tone: 'up' }
  ],
  commodities: [
    { label: 'WTI', value: '78.4', note: '정유와 운송 키워드가 갈림', tone: 'up' },
    { label: '금', value: '2,380', note: '안전자산 글에서 유지', tone: 'up' },
    { label: '원자재 반응', value: '+7%', note: '방산, 에너지 글에서 보조 지표로 등장', tone: 'neutral' },
    { label: '달러 영향', value: '중립', note: '원자재보다 환율 글로 분산', tone: 'neutral' }
  ]
};

const selectedGroup = computed(() => {
  const category = Array.isArray(route.params.category) ? route.params.category[0] : route.params.category;
  return marketGroups.find((group) => group.id === category) ?? null;
});

const domesticSectors: SectorTile[] = [
  { name: '반도체', direction: 'up', change: '+1.8%', heat: 92, keyword: 'HBM·장비' },
  { name: '로봇', direction: 'up', change: '+1.4%', heat: 76, keyword: '수주·공시' },
  { name: '금융', direction: 'up', change: '+0.9%', heat: 61, keyword: '배당·금리' },
  { name: '자동차', direction: 'up', change: '+0.6%', heat: 54, keyword: '환율·수출' },
  { name: '2차전지', direction: 'down', change: '-1.1%', heat: 68, keyword: '마진·수급' },
  { name: '바이오', direction: 'down', change: '-0.2%', heat: 43, keyword: '임상·공시' }
];

const usSectors: SectorTile[] = [
  { name: 'AI 반도체', direction: 'up', change: '+2.1%', heat: 94, keyword: 'GPU·서버' },
  { name: '빅테크', direction: 'up', change: '+0.8%', heat: 78, keyword: 'CAPEX' },
  { name: '에너지', direction: 'up', change: '+0.5%', heat: 52, keyword: 'WTI' },
  { name: '소비재', direction: 'down', change: '-0.7%', heat: 51, keyword: '소비 둔화' },
  { name: '헬스케어', direction: 'down', change: '-0.3%', heat: 46, keyword: '실적' },
  { name: '리츠', direction: 'down', change: '-1.3%', heat: 59, keyword: '금리' }
];

const anomalyRows = [
  { stock: 'NAVER', type: '가격 상승 · 부정 증가', price: '+0.7%', reaction: '부정 +14p', reason: '비용 우려' },
  { stock: '에코프로', type: '가격 하락 · 관심 증가', price: '-1.1%', reaction: '관심 +24%', reason: '수급 논쟁' },
  { stock: '한미반도체', type: '가격 상승 · 긍정 확산', price: '+2.3%', reaction: '긍정 +18p', reason: 'HBM 장비' },
  { stock: 'SOXS', type: 'ETF 상승 · 부정 우세', price: '+1.6%', reaction: '부정 +9p', reason: '변동성 회피' }
];

const schedules = [
  { date: '05.20', time: '03:00', title: 'FOMC 의사록', watch: '금리·환율 반응' },
  { date: '05.22', time: '21:30', title: '미국 CPI 수정치', watch: '성장주·채권' },
  { date: '05.23', time: '장중', title: '국내 주요 실적 발표', watch: '반도체 장비주' },
  { date: '05.24', time: '수시', title: '공시 일정 갱신', watch: '로봇·바이오' }
];

const freshnessRows = [
  { source: '국내 지수', state: '15분 지연', used: '국내주식 카드' },
  { source: '미국 지수', state: 'mock', used: '미국주식 카드' },
  { source: '환율·금리', state: '지연', used: '채권·환율 민감도' },
  { source: '커뮤니티 반응', state: '10:05 수집', used: '괴리 보드' }
];

const detailChartTicks = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00'];
</script>

<template>
  <section v-if="selectedGroup" class="surface-page indicators-page indicator-detail-page">
    <section class="indicator-detail-hero" :class="selectedGroup.tone">
      <RouterLink to="/indicators">전체 핵심 보기</RouterLink>
      <div>
        <p class="label">{{ selectedGroup.label }}</p>
        <h2>{{ selectedGroup.title }} 상세 지표</h2>
        <span>{{ selectedGroup.summary }}</span>
      </div>
      <strong>{{ selectedGroup.change }}</strong>
    </section>

    <section class="indicator-detail-kpi-grid" aria-label="상세 핵심 지표">
      <article v-for="row in detailRows[selectedGroup.id]" :key="row.label" :class="row.tone">
        <span>{{ row.label }}</span>
        <strong>{{ row.value }}</strong>
        <em>{{ row.note }}</em>
      </article>
    </section>

    <section class="indicator-detail-workbench">
      <article class="indicator-detail-chart-panel">
        <div class="section-band-title">
          <div>
            <p class="label">market x reaction</p>
            <h3>가격·반응 동시 변화</h3>
          </div>
          <span>mock trend</span>
        </div>
        <div class="indicator-chart-lines" aria-hidden="true">
          <svg viewBox="0 0 720 230" role="img">
            <defs>
              <linearGradient id="indicatorRedFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#ef4444" stop-opacity="0.18" />
                <stop offset="100%" stop-color="#ef4444" stop-opacity="0" />
              </linearGradient>
              <linearGradient id="indicatorBlueFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#2563eb" stop-opacity="0.16" />
                <stop offset="100%" stop-color="#2563eb" stop-opacity="0" />
              </linearGradient>
            </defs>
            <path d="M20 160 L120 136 L220 118 L320 132 L420 88 L540 74 L700 54 L700 214 L20 214 Z" fill="url(#indicatorRedFill)" />
            <path d="M20 178 L120 164 L220 172 L320 146 L420 152 L540 124 L700 136 L700 214 L20 214 Z" fill="url(#indicatorBlueFill)" />
            <polyline points="20,160 120,136 220,118 320,132 420,88 540,74 700,54" fill="none" stroke="#ef4444" stroke-width="4" stroke-linecap="round" />
            <polyline points="20,178 120,164 220,172 320,146 420,152 540,124 700,136" fill="none" stroke="#2563eb" stroke-width="4" stroke-linecap="round" />
          </svg>
          <div>
            <span v-for="tick in detailChartTicks" :key="tick">{{ tick }}</span>
          </div>
        </div>
      </article>

      <aside class="indicator-detail-side">
        <section>
          <p class="label">freshness</p>
          <h3>지표별 데이터 신선도</h3>
          <article v-for="row in freshnessRows" :key="row.source" class="freshness-row">
            <strong>{{ row.source }}</strong>
            <span>{{ row.state }}</span>
            <em>{{ row.used }}</em>
          </article>
        </section>
        <section>
          <p class="label">chips</p>
          <h3>연결 키워드</h3>
          <div class="theme-chip-map">
            <span v-for="chip in selectedGroup.chips" :key="chip" class="hot">{{ chip }}</span>
          </div>
        </section>
      </aside>
    </section>

    <section class="indicator-anomaly-panel detail-wide">
      <div class="section-band-title">
        <div>
          <p class="label">reaction anomaly</p>
          <h3>가격과 반응이 엇갈린 종목</h3>
        </div>
        <span>관찰 후보</span>
      </div>
      <div class="indicator-row-head">
        <span>종목</span><span>괴리</span><span>가격</span><span>반응</span><span>이유</span>
      </div>
      <article v-for="row in anomalyRows" :key="`${row.stock}-${row.type}`">
        <strong>{{ row.stock }}</strong>
        <span>{{ row.type }}</span>
        <em :class="row.price.startsWith('-') ? 'down' : 'up'">{{ row.price }}</em>
        <b>{{ row.reaction }}</b>
        <small>{{ row.reason }}</small>
      </article>
    </section>
  </section>

  <section v-else class="surface-page indicators-page indicator-hub-page">
    <section class="indicator-hub-hero" aria-labelledby="indicators-title">
      <div>
        <p class="label">market context</p>
        <h2 id="indicators-title">주요 지표</h2>
        <span>시장 지표 자체보다 커뮤니티 반응과 엇갈리는 구간을 먼저 봅니다.</span>
      </div>
      <div class="indicator-hub-clock">
        <strong>10:05</strong>
        <span>mock · 지연 혼합</span>
      </div>
    </section>

    <section class="indicator-core-grid" aria-label="핵심 지표 카테고리">
      <RouterLink
        v-for="group in marketGroups"
        :key="group.id"
        :class="['indicator-core-card', group.tone]"
        :to="`/indicators/${group.id}`"
      >
        <div class="indicator-core-top">
          <span>{{ group.label }}</span>
          <em>상세 분석으로 이동</em>
        </div>
        <strong>{{ group.title }}</strong>
        <b>{{ group.change }}</b>
        <p>{{ group.headline }}</p>
        <div class="indicator-chip-row">
          <small v-for="chip in group.chips" :key="chip">{{ chip }}</small>
        </div>
        <div class="indicator-mini-metrics">
          <span v-for="metric in group.metrics" :key="metric.name" :class="metric.tone">
            {{ metric.name }} <b>{{ metric.value }}</b>
          </span>
        </div>
      </RouterLink>
    </section>

    <section class="indicator-sector-layout">
      <article class="sector-map-panel">
        <div class="section-band-title">
          <div>
            <p class="label">sector breadth</p>
            <h3>국장 섹터 방향</h3>
          </div>
          <span>상승 4 · 하락 2</span>
        </div>
        <div class="sector-square-grid">
          <article
            v-for="sector in domesticSectors"
            :key="sector.name"
            :class="['sector-square', sector.direction]"
          >
            <strong>{{ sector.name }}</strong>
            <b>{{ sector.change }}</b>
            <span>{{ sector.keyword }}</span>
            <i><mark :style="{ width: `${sector.heat}%` }"></mark></i>
          </article>
        </div>
      </article>

      <article class="sector-map-panel">
        <div class="section-band-title">
          <div>
            <p class="label">sector breadth</p>
            <h3>미장 섹터 방향</h3>
          </div>
          <span>상승 3 · 하락 3</span>
        </div>
        <div class="sector-square-grid">
          <article
            v-for="sector in usSectors"
            :key="sector.name"
            :class="['sector-square', sector.direction]"
          >
            <strong>{{ sector.name }}</strong>
            <b>{{ sector.change }}</b>
            <span>{{ sector.keyword }}</span>
            <i><mark :style="{ width: `${sector.heat}%` }"></mark></i>
          </article>
        </div>
      </article>
    </section>

    <section class="indicator-lower-grid">
      <article class="indicator-anomaly-panel">
        <div class="section-band-title">
          <div>
            <p class="label">reaction anomaly</p>
            <h3>가격과 반응이 엇갈린 종목</h3>
          </div>
          <span>관찰 후보</span>
        </div>
        <div class="indicator-row-head">
          <span>종목</span><span>괴리</span><span>가격</span><span>반응</span><span>이유</span>
        </div>
        <article v-for="row in anomalyRows" :key="`${row.stock}-${row.type}`">
          <strong>{{ row.stock }}</strong>
          <span>{{ row.type }}</span>
          <em :class="row.price.startsWith('-') ? 'down' : 'up'">{{ row.price }}</em>
          <b>{{ row.reaction }}</b>
          <small>{{ row.reason }}</small>
        </article>
      </article>

      <aside class="indicator-side-stack">
        <section>
          <div class="section-band-title compact">
            <div>
              <p class="label">theme heatmap</p>
              <h3>섹터·테마별 반응 히트맵</h3>
            </div>
          </div>
          <div class="theme-chip-map">
            <span class="hot">반도체 92</span>
            <span class="hot">미국주식 82</span>
            <span>2차전지 76</span>
            <span>로봇 69</span>
            <span class="cool">바이오 48</span>
            <span class="cool">배당 35</span>
          </div>
        </section>

        <section>
          <div class="section-band-title compact">
            <div>
              <p class="label">freshness</p>
              <h3>지표별 데이터 신선도</h3>
            </div>
          </div>
          <article v-for="row in freshnessRows" :key="row.source" class="freshness-row">
            <strong>{{ row.source }}</strong>
            <span>{{ row.state }}</span>
            <em>{{ row.used }}</em>
          </article>
        </section>
      </aside>
    </section>

    <section class="indicator-schedule-strip" aria-label="주요 일정">
      <div class="section-band-title full">
        <div>
          <p class="label">calendar</p>
          <h3>주요 일정</h3>
        </div>
        <span>CPI · FOMC · 실적 · 공시</span>
      </div>
      <article v-for="schedule in schedules" :key="`${schedule.date}-${schedule.title}`">
        <time>{{ schedule.date }}</time>
        <span>{{ schedule.time }}</span>
        <strong>{{ schedule.title }}</strong>
        <em>{{ schedule.watch }}</em>
      </article>
    </section>
  </section>
</template>
