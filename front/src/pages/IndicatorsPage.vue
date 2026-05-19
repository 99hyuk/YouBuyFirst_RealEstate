<script setup lang="ts">
const marketIndicators = [
  { name: 'KOSPI', value: '2,742.18', change: '+0.44%', state: '지연', reaction: '+12%', link: '반도체 언급 증가' },
  { name: 'KOSDAQ', value: '874.32', change: '-0.31%', state: '지연', reaction: '+24%', link: '2차전지 관심 증가' },
  { name: 'NASDAQ', value: '16,340.87', change: '+0.72%', state: 'mock', reaction: '+16%', link: '미국주식 글 증가' },
  { name: 'USD/KRW', value: '1,350.20', change: '-0.18%', state: '지연', reaction: '+8%', link: '환율 민감주 언급' },
  { name: 'VIX', value: '14.8', change: '+2.1%', state: 'mock', reaction: '+11%', link: '방어주 키워드' },
  { name: '미국 10Y', value: '4.41%', change: '+0.03p', state: 'mock', reaction: '+9%', link: '성장주 부담' },
  { name: 'SOX', value: '5,218.4', change: '+1.12%', state: 'mock', reaction: '+31%', link: 'HBM·장비' },
  { name: 'KRW BTC', value: '91.2M', change: '-0.8%', state: '지연', reaction: '+6%', link: '코인 관련주' },
  { name: 'WTI', value: '78.4', change: '+0.6%', state: 'mock', reaction: '+4%', link: '정유·운송' },
  { name: '금 선물', value: '2,380', change: '+0.2%', state: 'mock', reaction: '+7%', link: '안전자산' },
  { name: '공포탐욕', value: '61', change: '-2p', state: 'mock', reaction: '+10%', link: '레버리지 ETF' },
  { name: 'KRX 반도체', value: '4,912', change: '+1.4%', state: '지연', reaction: '+28%', link: '장비주 언급' }
];

const anomalyRows = [
  { stock: 'NAVER', type: '가격 상승 · 부정 증가', price: '+0.7%', reaction: '부정 +14p', reason: '비용 우려' },
  { stock: '에코프로', type: '가격 하락 · 관심 증가', price: '-1.1%', reaction: '관심 +24%', reason: '수급 뉴스' },
  { stock: '한미반도체', type: '가격 상승 · 긍정 확산', price: '+2.3%', reaction: '긍정 +18p', reason: 'HBM 키워드' },
  { stock: '로봇 테마', type: '지수 약세 · 테마 강세', price: '-0.4%', reaction: '언급 +19%', reason: '공시 일정' },
  { stock: 'SOXS', type: 'ETF 상승 · 부정 우세', price: '+1.6%', reaction: '부정 +9p', reason: '변동성 회피' },
  { stock: '삼성SDI', type: '가격 정체 · 관심 증가', price: '+0.1%', reaction: '관심 +17%', reason: '실적 대기' }
];

const themeHeatmap = [
  { theme: '반도체', heat: 92, change: '+18p' },
  { theme: '미국주식', heat: 82, change: '+11p' },
  { theme: '2차전지', heat: 76, change: '+24p' },
  { theme: '로봇', heat: 69, change: '+9p' },
  { theme: '바이오', heat: 48, change: '-3p' },
  { theme: '배당', heat: 35, change: '+2p' },
  { theme: '환율', heat: 52, change: '+6p' },
  { theme: '금리', heat: 44, change: '+5p' }
];

const sectorBreadthGroups = [
  {
    market: '국장',
    caption: 'KRX 주요 섹터 · 15분 지연',
    summary: { primary: '4:2', state: '상승 우세', up: 4, down: 2 },
    note: '반도체·금융 쪽은 강하고 2차전지는 약한 흐름',
    sectors: [
      { name: '반도체', focus: 'HBM·장비', direction: 'up', intensity: 68, change: '+1.8%' },
      { name: '자동차', focus: '환율·수출', direction: 'up', intensity: 54, change: '+0.6%' },
      { name: '금융', focus: '배당·금리', direction: 'up', intensity: 61, change: '+0.9%' },
      { name: '2차전지', focus: '수급·마진', direction: 'down', intensity: 52, change: '-1.1%' },
      { name: '바이오', focus: '임상·공시', direction: 'down', intensity: 43, change: '-0.2%' },
      { name: '로봇', focus: '정책·수주', direction: 'up', intensity: 63, change: '+1.4%' }
    ]
  },
  {
    market: '미장',
    caption: 'S&P/NASDAQ 대표 섹터 · mock',
    summary: { primary: '3:3', state: '혼조', up: 3, down: 3 },
    note: 'AI/반도체는 강하지만 소비재와 금리 민감주는 약세',
    sectors: [
      { name: 'AI/반도체', focus: 'GPU·서버', direction: 'up', intensity: 72, change: '+2.1%' },
      { name: '빅테크', focus: '실적·CAPEX', direction: 'up', intensity: 58, change: '+0.8%' },
      { name: '소비재', focus: '소비 둔화', direction: 'down', intensity: 51, change: '-0.7%' },
      { name: '헬스케어', focus: '규제·실적', direction: 'down', intensity: 46, change: '-0.3%' },
      { name: '에너지', focus: 'WTI·정제', direction: 'up', intensity: 52, change: '+0.5%' },
      { name: '리츠/유틸', focus: '금리 민감', direction: 'down', intensity: 59, change: '-1.3%' }
    ]
  }
];

const schedules = [
  { date: '05.20', time: '03:00', title: 'FOMC 의사록', watch: '금리·나스닥 반응' },
  { date: '05.22', time: '21:30', title: '미국 CPI 수정치', watch: '환율·성장주' },
  { date: '05.23', time: '장중', title: '국내 주요 실적 발표', watch: '대형주 댓글 속도' },
  { date: '05.24', time: '수시', title: '공시 일정 갱신', watch: '로봇·바이오' },
  { date: '05.25', time: '장전', title: '기관 수급 잠정치', watch: '반도체·2차전지' },
  { date: '05.26', time: '장후', title: '미국 PCE 대기', watch: '환율 민감 글' }
];

const freshnessRows = [
  { source: '국내 지수', state: '15분 지연', used: '홈·주요 지표' },
  { source: '미국 지수', state: 'mock', used: '야간 반응 테스트' },
  { source: '환율', state: '지연', used: '해외주식 글 연결' },
  { source: '커뮤니티 반응', state: '10:05 수집', used: '괴리 보드' },
  { source: '공시 일정', state: 'mock', used: '이벤트 타임라인' },
  { source: '섹터 분류', state: '수동 매핑', used: '테마 히트맵' }
];
</script>

<template>
  <section class="surface-page indicators-page market-density-page">
    <section class="market-command-board" aria-labelledby="indicators-title">
      <div class="terminal-title-row">
        <div>
          <p class="label">market context</p>
          <h2 id="indicators-title">주요 지표</h2>
          <span>시장 지표 자체보다 커뮤니티 반응과 엇갈리는 구간을 먼저 봅니다.</span>
        </div>
        <span class="status-pill warning">실시간/지연/mock 혼재</span>
      </div>

      <section class="market-tape-grid" aria-label="시장 지표와 데이터 신선도">
        <article v-for="indicator in marketIndicators" :key="indicator.name">
          <div>
            <span>{{ indicator.name }}</span>
            <strong>{{ indicator.value }}</strong>
          </div>
          <em :class="indicator.change.startsWith('-') ? 'down' : 'up'">{{ indicator.change }}</em>
          <small>{{ indicator.state }}</small>
          <p>{{ indicator.link }} · 반응 {{ indicator.reaction }}</p>
        </article>
      </section>

      <section class="sector-breadth-grid" aria-label="국장과 미장 섹터 방향">
        <article v-for="group in sectorBreadthGroups" :key="group.market" class="sector-breadth-card">
          <div class="table-caption">
            <div>
              <p class="label">sector breadth</p>
              <h3>{{ group.market }} 섹터 방향</h3>
            </div>
            <span class="status-pill subtle">{{ group.caption }}</span>
          </div>
          <div class="sector-breadth-summary">
            <strong>{{ group.summary.primary }}</strong>
            <span>{{ group.summary.state }}</span>
            <em>상승 {{ group.summary.up }} · 하락 {{ group.summary.down }}</em>
            <small>{{ group.note }}</small>
          </div>
          <div class="sector-tile-grid">
            <article
              v-for="sector in group.sectors"
              :key="`${group.market}-${sector.name}`"
              :class="['sector-tile', sector.direction]"
            >
              <div>
                <strong>{{ sector.name }}</strong>
                <span>{{ sector.focus }}</span>
              </div>
              <em>{{ sector.change }}</em>
              <small>{{ sector.direction === 'up' ? '상승' : '하락' }} · 강도 {{ sector.intensity }}</small>
            </article>
          </div>
        </article>
      </section>

      <section class="market-split-grid">
        <div class="market-anomaly-table">
          <div class="table-caption">
            <div>
              <p class="label">reaction anomaly</p>
              <h3>가격과 반응이 엇갈린 종목</h3>
            </div>
            <span class="status-pill subtle">관찰 후보</span>
          </div>
          <div class="anomaly-head">
            <span>종목</span><span>괴리</span><span>가격</span><span>반응</span><span>키워드</span>
          </div>
          <article v-for="row in anomalyRows" :key="`${row.stock}-${row.reason}`">
            <strong>{{ row.stock }}</strong>
            <span>{{ row.type }}</span>
            <em :class="row.price.startsWith('-') ? 'down' : 'up'">{{ row.price }}</em>
            <b>{{ row.reaction }}</b>
            <small>{{ row.reason }}</small>
          </article>
        </div>

        <aside class="theme-terminal">
          <div>
            <p class="label">theme heatmap</p>
            <h3>섹터·테마별 반응 히트맵</h3>
          </div>
          <article v-for="item in themeHeatmap" :key="item.theme">
            <strong>{{ item.theme }}</strong>
            <i><mark :style="{ width: `${item.heat}%` }"></mark></i>
            <span>{{ item.heat }}</span>
            <em>{{ item.change }}</em>
          </article>
        </aside>
      </section>

      <section class="market-bottom-grid">
        <div class="schedule-terminal">
          <div class="table-caption">
            <div>
              <p class="label">calendar</p>
              <h3>주요 일정</h3>
            </div>
          </div>
          <article v-for="schedule in schedules" :key="`${schedule.date}-${schedule.title}`">
            <time>{{ schedule.date }}</time>
            <span>{{ schedule.time }}</span>
            <strong>{{ schedule.title }}</strong>
            <em>{{ schedule.watch }}</em>
          </article>
        </div>
        <div class="freshness-terminal">
          <div class="table-caption">
            <div>
              <p class="label">freshness</p>
              <h3>지표별 데이터 신선도</h3>
            </div>
          </div>
          <article v-for="row in freshnessRows" :key="row.source">
            <strong>{{ row.source }}</strong>
            <span>{{ row.state }}</span>
            <em>{{ row.used }}</em>
          </article>
        </div>
      </section>
    </section>
  </section>
</template>
