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

type IndicatorItem = {
  category: string;
  name: string;
  value: string;
  note: string;
  tone: Tone;
};

type RegionTile = {
  name: string;
  direction: 'up' | 'down';
  change: string;
  heat: number;
  keyword: string;
};

const route = useRoute();

const marketGroups: MarketGroup[] = [
  {
    id: 'price-transaction',
    label: 'price & volume',
    title: '가격 및 거래량',
    headline: '실거래가와 거래량이 방향을 먼저 갈라줍니다',
    change: '+0.31%',
    tone: 'up',
    summary: '매매·전세가격지수, 실거래가 지수, 매매·전월세 거래량을 함께 보며 가격 흐름과 거래 강도를 분리합니다.',
    chips: ['매매가격지수 101.8', '실거래가 지수 103.4', '거래량 -6.8%'],
    metrics: [
      { name: '매매가격지수', value: '101.8', tone: 'up' },
      { name: '전세가격지수', value: '100.9', tone: 'up' },
      { name: '거래량', value: '8.4만건', tone: 'down' }
    ]
  },
  {
    id: 'supply-demand',
    label: 'supply balance',
    title: '공급 및 수급',
    headline: '미분양과 착공 감소는 2~3년 뒤를 보는 선행 신호입니다',
    change: '-3.2%',
    tone: 'down',
    summary: '미분양, 준공 후 미분양, 인허가·착공·준공 실적, 전세가율을 묶어 공급 부담과 실수요 압력을 봅니다.',
    chips: ['미분양 5.7만호', '착공 -11.4%', '전세가율 62.4%'],
    metrics: [
      { name: '준공 후 미분양', value: '1.2만호', tone: 'down' },
      { name: '인허가', value: '-8.1%', tone: 'down' },
      { name: '전세가율', value: '62.4%', tone: 'up' }
    ]
  },
  {
    id: 'sentiment-demand',
    label: 'demand mood',
    title: '수요 및 심리',
    headline: '수급지수와 소비심리가 가격보다 먼저 방향을 암시합니다',
    change: '+4.8p',
    tone: 'up',
    summary: '매매수급동향, 전세수급동향, 부동산시장 소비심리지수를 기준선 100과 비교해 수요 우위를 확인합니다.',
    chips: ['매매수급 104.2', '전세수급 107.8', '소비심리 112.5'],
    metrics: [
      { name: '매매수급지수', value: '104.2', tone: 'up' },
      { name: '전세수급지수', value: '107.8', tone: 'up' },
      { name: '소비심리지수', value: '112.5', tone: 'up' }
    ]
  },
  {
    id: 'macro-finance',
    label: 'macro finance',
    title: '거시경제 및 금융',
    headline: '구매력과 자금 조달 비용이 지역 반응의 상한선을 만듭니다',
    change: '3.50%',
    tone: 'neutral',
    summary: '주택구입부담지수, 기준금리, 통화량 M2, 물가상승률을 함께 보며 자금 유입 가능성과 부담을 분리합니다.',
    chips: ['K-HAI 172.4', '기준금리 3.50%', 'M2 +5.1%'],
    metrics: [
      { name: 'K-HAI', value: '172.4', tone: 'down' },
      { name: '기준금리', value: '3.50%', tone: 'neutral' },
      { name: '물가상승률', value: '2.7%', tone: 'neutral' }
    ]
  }
];

const detailRows: Record<string, { label: string; value: string; note: string; tone: Tone }[]> = {
  'price-transaction': [
    { label: '매매가격지수', value: '101.8', note: '기준 시점 100 대비 가격 레벨을 비교합니다.', tone: 'up' },
    { label: '전세가격지수', value: '100.9', note: '전세 압력이 매매 전환 수요로 이어지는지 봅니다.', tone: 'up' },
    { label: '실거래가 지수', value: '103.4', note: '실제 계약가 기반이라 후행이지만 방향 신뢰도가 높습니다.', tone: 'up' },
    { label: '매매·전월세 거래량', value: '8.4만건', note: '평년 대비 급감하면 관망 또는 침체 신호로 봅니다.', tone: 'down' }
  ],
  'supply-demand': [
    { label: '미분양 주택', value: '5.7만호', note: '감소는 분양 소화, 증가는 공급 부담으로 읽습니다.', tone: 'down' },
    { label: '준공 후 미분양', value: '1.2만호', note: '악성 미분양으로 분리해 더 강한 침체 신호로 봅니다.', tone: 'down' },
    { label: '인허가·착공·준공', value: '-11.4%', note: '착공 감소는 2~3년 뒤 입주 부족 후보입니다.', tone: 'down' },
    { label: '전세가율', value: '62.4%', note: '높을수록 실수요 기반과 매매 전환 압력을 같이 봅니다.', tone: 'up' }
  ],
  'sentiment-demand': [
    { label: '매매수급지수', value: '104.2', note: '100보다 높으면 수요가 공급보다 많다는 뜻입니다.', tone: 'up' },
    { label: '전세수급지수', value: '107.8', note: '전세 매물 부족 체감과 함께 확인합니다.', tone: 'up' },
    { label: '소비심리지수', value: '112.5', note: '중개업소와 가구 설문 기반의 선행 심리 지표입니다.', tone: 'up' },
    { label: '커뮤니티 언급량', value: '+38%', note: '공식 심리 지표가 늦게 반영하는 체감 변화를 보조합니다.', tone: 'up' }
  ],
  'macro-finance': [
    { label: '주택구입부담지수(K-HAI)', value: '172.4', note: '높을수록 중간 소득 가구의 구매력이 떨어집니다.', tone: 'down' },
    { label: '기준금리', value: '3.50%', note: '담보대출 금리와 수요 자극 가능성을 연결해 봅니다.', tone: 'neutral' },
    { label: '통화량(M2)', value: '+5.1%', note: '시중 유동성이 부동산으로 유입될 여지를 봅니다.', tone: 'up' },
    { label: '물가상승률', value: '2.7%', note: '실질 구매력과 금리 경로를 같이 판단합니다.', tone: 'neutral' }
  ]
};

const selectedGroup = computed(() => {
  const category = Array.isArray(route.params.category) ? route.params.category[0] : route.params.category;
  return marketGroups.find((group) => group.id === category) ?? null;
});

const regionTiles: RegionTile[] = [
  { name: '서울 핵심지', direction: 'up', change: '+0.42%', heat: 88, keyword: '전세가율·수급' },
  { name: '수도권 외곽', direction: 'down', change: '-0.18%', heat: 54, keyword: '거래량 둔화' },
  { name: '광역시', direction: 'up', change: '+0.12%', heat: 61, keyword: '미분양 감소' },
  { name: '지방 중소도시', direction: 'down', change: '-0.24%', heat: 48, keyword: '준공 후 미분양' },
  { name: '전세 압력 지역', direction: 'up', change: '+0.37%', heat: 77, keyword: '전세수급 100+' },
  { name: '입주 부담 지역', direction: 'down', change: '-0.31%', heat: 59, keyword: '준공 물량' }
];

const anomalyRows = [
  { target: '마포구 아파트', type: '전세수급 상승 · 거래량 둔화', price: '+0.18%', reaction: '우려 +21p', reason: '전세 매물 감소' },
  { target: '동탄역권', type: '교통 기대 · 입주 물량 부담', price: '+0.11%', reaction: '관심 +38%', reason: 'GTX·입주 논쟁' },
  { target: '송도국제도시', type: '미분양 부담 · 학군 기대 공존', price: '-0.16%', reaction: '중립 42%', reason: '공급 소화 확인 필요' },
  { target: '분당·판교', type: '매매수급 우위 · 가격 지연', price: '+0.27%', reaction: '기대 +26p', reason: '재건축·일자리' }
];

const schedules = [
  { date: '06.03', time: '주간', title: '한국부동산원 주간 가격동향', watch: '매매·전세가격지수' },
  { date: '06.05', time: '월간', title: '실거래가 지수 갱신', watch: '신고 지연 보정' },
  { date: '06.10', time: '월간', title: '미분양·인허가 통계', watch: '준공 후 미분양' },
  { date: '06.12', time: '수시', title: '기준금리·대출 금리 변화', watch: 'K-HAI·수요 심리' }
];

const freshnessRows = [
  { source: '한국부동산원 가격지수', state: '주간 공개', used: '매매·전세가격지수' },
  { source: '국토부 실거래가', state: '신고·공개 지연', used: '실거래가 지수·거래량' },
  { source: '국토부 주택통계', state: '월간 공개', used: '미분양·인허가·착공·준공' },
  { source: '한국은행·통계청', state: '월간·수시', used: '기준금리·M2·물가' }
];

const themeChips = ['매매가격지수 101.8', '전세가율 62.4%', '미분양 5.7만호', '매매수급 104.2', 'K-HAI 172.4', 'M2 +5.1%'];
const detailChartTicks = ['D-30', 'D-21', 'D-14', 'D-7', 'D-3', '현재'];
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
            <p class="label">indicator x reaction</p>
            <h3>지표와 지역 반응 동시 변화</h3>
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
          <h3>지표와 반응이 엇갈린 지역</h3>
        </div>
        <span>관찰 후보</span>
      </div>
      <div class="indicator-row-head">
        <span>지역/단지</span><span>괴리</span><span>지표</span><span>반응</span><span>이유</span>
      </div>
      <article v-for="row in anomalyRows" :key="`${row.target}-${row.type}`">
        <strong>{{ row.target }}</strong>
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
        <p class="label">real estate context</p>
        <h2 id="indicators-title">주요 지표</h2>
        <span>가격·거래량, 공급·수급, 수요·심리, 거시·금융 지표를 지역 반응과 함께 봅니다.</span>
      </div>
      <div class="indicator-hub-clock">
        <strong>10:05</strong>
        <span>mock · 공개 지연 혼합</span>
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
            <p class="label">regional breadth</p>
            <h3>지역별 지표 방향</h3>
          </div>
          <span>상승 3 · 하락 3</span>
        </div>
        <div class="sector-square-grid">
          <article
            v-for="tile in regionTiles"
            :key="tile.name"
            :class="['sector-square', tile.direction]"
          >
            <strong>{{ tile.name }}</strong>
            <b>{{ tile.change }}</b>
            <span>{{ tile.keyword }}</span>
            <i><mark :style="{ width: `${tile.heat}%` }"></mark></i>
          </article>
        </div>
      </article>

      <article class="sector-map-panel">
        <div class="section-band-title">
          <div>
            <p class="label">indicator map</p>
            <h3>지표 묶음별 관찰 포인트</h3>
          </div>
          <span>가격 · 공급 · 심리 · 금융</span>
        </div>
        <div class="sector-square-grid">
          <article v-for="item in marketGroups" :key="item.id" :class="['sector-square', item.tone === 'down' ? 'down' : 'up']">
            <strong>{{ item.title }}</strong>
            <b>{{ item.change }}</b>
            <span>{{ item.headline }}</span>
            <i><mark :style="{ width: item.tone === 'neutral' ? '58%' : '78%' }"></mark></i>
          </article>
        </div>
      </article>
    </section>

    <section class="indicator-lower-grid">
      <article class="indicator-anomaly-panel">
        <div class="section-band-title">
          <div>
            <p class="label">reaction anomaly</p>
            <h3>지표와 반응이 엇갈린 지역</h3>
          </div>
          <span>관찰 후보</span>
        </div>
        <div class="indicator-row-head">
          <span>지역/단지</span><span>괴리</span><span>지표</span><span>반응</span><span>이유</span>
        </div>
        <article v-for="row in anomalyRows" :key="`${row.target}-${row.type}`">
          <strong>{{ row.target }}</strong>
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
              <p class="label">indicator heatmap</p>
              <h3>지표별 반응 히트맵</h3>
            </div>
          </div>
          <div class="theme-chip-map">
            <span v-for="chip in themeChips" :key="chip" :class="chip.includes('K-HAI') ? 'cool' : 'hot'">{{ chip }}</span>
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
        <span>가격지수 · 실거래 · 미분양 · 금리</span>
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
