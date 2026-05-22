<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

type Tone = 'positive' | 'negative' | 'watch' | 'neutral';

type SignalTile = {
  label: string;
  stock: string;
  symbol: string;
  metric: string;
  tone: Tone;
  summary: string;
  reasons: string[];
  pulse: number;
  community: string;
};

type CommunityPulse = {
  name: string;
  status: string;
  topStock: string;
  mention: number;
  positive: number;
  negative: number;
  theme: string;
};

type StrategySeries = {
  name: string;
  tone: 'follow' | 'reverse';
  returnPct: string;
  hitRate: string;
  drawdown: string;
  points: string;
};

type AgentLog = {
  time: string;
  strategy: '지표 추종' | '커뮤니티 역추종';
  stock: string;
  symbol: string;
  state: string;
  input: string;
  reason: string;
  key: string;
};

const route = useRoute();
const activeHumanView = computed(() => {
  const view = route.query.view;
  return Array.isArray(view) ? view[0] ?? 'overview' : view ?? 'overview';
});

const humanViewTabs = [
  { label: '반응 한눈에', view: 'overview', to: { path: '/communities' } },
  { label: '성과 비교', view: 'experiments', to: { path: '/communities', query: { view: 'experiments' } } },
  { label: '모의 에이전트', view: 'agents', to: { path: '/communities', query: { view: 'agents' } } }
];

const signalTiles: SignalTile[] = [
  {
    label: '지금 뜨는 종목',
    stock: '두산로보틱스',
    symbol: '454910',
    metric: '+42%',
    tone: 'positive',
    summary: '로봇 수주 키워드와 인기글 상위권이 같이 붙었습니다.',
    reasons: ['에펨코리아 상위 2% 글', '댓글 속도 1.8배', '가격 +4.8% 동시'],
    pulse: 88,
    community: '에펨코리아'
  },
  {
    label: '부정적인 종목',
    stock: 'NAVER',
    symbol: '035420',
    metric: '부정 48',
    tone: 'negative',
    summary: '비용 부담, 광고 둔화, AI 투자비 키워드가 반복됩니다.',
    reasons: ['뽐뿌 비용 우려', '종토방 실적 논쟁', '출처 편중 58%'],
    pulse: 64,
    community: '뽐뿌 증권포럼'
  },
  {
    label: '언급 많은 종목',
    stock: '삼성전자',
    symbol: '005930',
    metric: '18.4M',
    tone: 'watch',
    summary: 'HBM, 서버 수요, 외국인 수급 이야기가 넓게 퍼졌습니다.',
    reasons: ['네이버 종토방 급증', '반도체 테마 1위', '출처 4곳 이상'],
    pulse: 76,
    community: '네이버 종토방'
  },
  {
    label: '라이징 스타',
    stock: '한미반도체',
    symbol: '042700',
    metric: '+22%',
    tone: 'positive',
    summary: '장비 수주와 실적 기대 키워드가 짧은 시간에 올라왔습니다.',
    reasons: ['토스 관심 등록 증가', '장비 수주 키워드', '긍정 57 / 부정 22'],
    pulse: 72,
    community: '토스증권 커뮤니티'
  }
];

const communityPulses: CommunityPulse[] = [
  { name: '네이버 종토방', status: 'local-research-only', topStock: '삼성전자', mention: 92, positive: 41, negative: 33, theme: '반도체' },
  { name: '디시 주식', status: 'public-demo-only', topStock: '에코프로', mention: 78, positive: 48, negative: 37, theme: '2차전지' },
  { name: '뽐뿌 증권포럼', status: 'enabled', topStock: 'NAVER', mention: 61, positive: 36, negative: 42, theme: '플랫폼' },
  { name: '에펨코리아', status: 'public-demo-only', topStock: '두산로보틱스', mention: 84, positive: 61, negative: 18, theme: '로봇' },
  { name: '토스증권', status: 'public-demo-only', topStock: '한미반도체', mention: 69, positive: 57, negative: 22, theme: '장비' },
  { name: '블라인드', status: 'local-research-only', topStock: 'SOXS', mention: 57, positive: 28, negative: 51, theme: '미국주식' }
];

const strategySeries: StrategySeries[] = [
  {
    name: '지표 추종',
    tone: 'follow',
    returnPct: '+3.1%',
    hitRate: '55%',
    drawdown: '-3.8%',
    points: '0,82 58,74 116,64 174,67 232,51 290,42 348,34 406,28'
  },
  {
    name: '커뮤니티 역추종',
    tone: 'reverse',
    returnPct: '+1.7%',
    hitRate: '49%',
    drawdown: '-5.4%',
    points: '0,86 58,80 116,76 174,70 232,73 290,61 348,58 406,49'
  }
];

const agentLogs: AgentLog[] = [
  {
    time: '10:12',
    strategy: '지표 추종',
    stock: '두산로보틱스',
    symbol: '454910',
    state: 'paper 후보',
    input: '언급 +42% · 긍정 61 · 가격 +4.8%',
    reason: '인기글 상위권과 가격 흐름이 같은 방향',
    key: 'follow-v2-454910-1012'
  },
  {
    time: '10:04',
    strategy: '커뮤니티 역추종',
    stock: 'NAVER',
    symbol: '035420',
    state: '관찰만',
    input: '부정 48 · 출처 편중 58% · 가격 +0.7%',
    reason: '부정 반응은 강하지만 표본이 한쪽으로 치우침',
    key: 'reverse-v1-035420-1004'
  },
  {
    time: '09:51',
    strategy: '지표 추종',
    stock: '삼성전자',
    symbol: '005930',
    state: '관찰 유지',
    input: '언급 18.4M · 긍정 54 · 출처 4곳',
    reason: '반도체 테마와 수급 키워드가 동시에 증가',
    key: 'follow-v2-005930-0951'
  },
  {
    time: '09:37',
    strategy: '커뮤니티 역추종',
    stock: '에코프로',
    symbol: '086520',
    state: '스킵',
    input: '관심 +24% · 부정 46 · 가격 -1.1%',
    reason: '관심은 늘었지만 가격과 반응 방향이 엇갈림',
    key: 'reverse-v1-086520-0937'
  }
];

const strategyRules = [
  { name: '지표 추종', version: 'follow-v2', rule: '언급 증가, 긍정 비율, 가격 snapshot이 같은 방향일 때만 paper 후보로 둡니다.', keys: 9 },
  { name: '커뮤니티 역추종', version: 'reverse-v1', rule: '과열·부정 편중·가격 괴리가 커질 때 관찰하거나 스킵 사유를 남깁니다.', keys: 6 }
];
</script>

<template>
  <section class="surface-page communities-page human-dashboard-page">
    <section class="human-hero-panel" aria-labelledby="human-title">
      <div class="human-hero-copy">
        <p class="label">human indicator</p>
        <h2 id="human-title">인간 지표</h2>
        <span>커뮤니티 반응을 종목 신호, 성과 실험, 모의 에이전트 판단 기록으로 압축해 봅니다.</span>
      </div>
      <nav class="human-view-tabs compact" aria-label="인간 지표 하위 화면">
        <RouterLink
          v-for="tab in humanViewTabs"
          :key="tab.view"
          :class="{ active: activeHumanView === tab.view }"
          :to="tab.to"
        >
          {{ tab.label }}
        </RouterLink>
      </nav>
    </section>

    <section class="human-signal-board" aria-label="커뮤니티별 언급 급증 종목">
      <div class="section-band-title full">
        <div>
          <p class="label">signal board</p>
          <h3>커뮤니티별 언급 급증 종목</h3>
        </div>
        <span>인기글·개념글 레이어에서 강하게 뜬 종목만 짧게 표시</span>
      </div>
      <RouterLink
        v-for="tile in signalTiles"
        :key="tile.label"
        :class="['human-signal-tile', tile.tone]"
        :to="`/stocks/${tile.symbol}`"
      >
        <div class="signal-tile-top">
          <span>{{ tile.label }}</span>
          <em>{{ tile.community }}</em>
        </div>
        <strong>{{ tile.stock }}</strong>
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

    <section class="human-main-grid">
      <article class="human-performance-panel">
        <div class="section-band-title">
          <div>
            <p class="label">paper experiment</p>
            <h3>커뮤니티 에이전트 수익률 비교 그래프</h3>
          </div>
          <span>커뮤니티별 성과 실험 · 1D · 7D · 1M · 3M mock</span>
        </div>
        <div class="human-chart-shell">
          <svg viewBox="0 0 430 130" role="img" aria-label="지표 추종과 커뮤니티 역추종 수익률 비교">
            <line x1="0" y1="100" x2="420" y2="100" />
            <line x1="0" y1="68" x2="420" y2="68" />
            <line x1="0" y1="36" x2="420" y2="36" />
            <polyline
              v-for="series in strategySeries"
              :key="series.name"
              :class="series.tone"
              :points="series.points"
            />
          </svg>
          <div class="human-chart-legend">
            <article v-for="series in strategySeries" :key="series.name">
              <i :class="series.tone"></i>
              <strong>{{ series.name }}</strong>
              <em>{{ series.returnPct }}</em>
              <span>적중 {{ series.hitRate }} · 최대 낙폭 {{ series.drawdown }}</span>
            </article>
          </div>
        </div>
      </article>

      <aside class="human-rule-stack">
        <article v-for="rule in strategyRules" :key="rule.version">
          <span>{{ rule.version }}</span>
          <strong>{{ rule.name }}</strong>
          <p>{{ rule.rule }}</p>
          <em>판단 key {{ rule.keys }}개</em>
        </article>
      </aside>
    </section>

    <section class="human-community-grid" aria-label="커뮤니티별 반응 비교">
      <div class="section-band-title full">
        <div>
          <p class="label">community pulse</p>
          <h3>커뮤니티별 언급 급증과 반응 비율</h3>
        </div>
        <span>커뮤니티별 반응 비교 · 수집 상태 · 언급량 · 긍정/부정 비율</span>
      </div>
      <article v-for="community in communityPulses" :key="community.name" class="human-community-tile">
        <div>
          <strong>{{ community.name }}</strong>
          <span>{{ community.status }}</span>
        </div>
        <b>{{ community.topStock }}</b>
        <i class="mention-meter">
          <mark :style="{ width: `${community.mention}%` }"></mark>
        </i>
        <div class="tone-meter">
          <span class="positive" :style="{ width: `${community.positive}%` }"></span>
          <span class="negative" :style="{ width: `${community.negative}%` }"></span>
        </div>
        <em>{{ community.theme }} · 긍정 {{ community.positive }} / 부정 {{ community.negative }}</em>
      </article>
    </section>

    <section id="agent-simulation" class="human-agent-section compact-ledger" aria-labelledby="human-agent-title">
      <div class="section-band-title">
        <div>
          <p class="label">agent simulation</p>
          <h3 id="human-agent-title">모의 에이전트 판단 기록</h3>
        </div>
        <span>최근 판단 로그 · 인간 지표 기반 · 실거래 아님</span>
      </div>

      <div class="agent-log-board">
        <div class="agent-log-head">
          <span>시간</span>
          <span>종목</span>
          <span>전략</span>
          <span>상태</span>
          <span>판단 입력값</span>
          <span>판단 key</span>
        </div>
        <RouterLink
          v-for="log in agentLogs"
          :key="log.key"
          class="agent-log-row"
          :to="`/stocks/${log.symbol}`"
        >
          <time>{{ log.time }}</time>
          <strong>{{ log.stock }}</strong>
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
