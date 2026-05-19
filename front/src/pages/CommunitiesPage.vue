<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const activeHumanView = computed(() => {
  const view = route.query.view;
  return Array.isArray(view) ? view[0] ?? 'overview' : view ?? 'overview';
});

const humanViewTabs = [
  { label: '커뮤니티 반응', view: 'overview', to: { path: '/communities' } },
  { label: '성과 실험', view: 'experiments', to: { path: '/communities', query: { view: 'experiments' } } },
  { label: '모의 에이전트', view: 'agents', to: { path: '/communities', query: { view: 'agents' } } }
];

const communities = [
  { name: '네이버 종토방', status: 'local-research-only', lastCollected: '10:03', skipReason: '본문 일부만 저장', surge: '삼성전자', positive: 41, negative: 33, theme: '반도체·대형주' },
  { name: '디시 주식', status: 'public-demo-only', lastCollected: '10:01', skipReason: '속도 제한 관찰', surge: '에코프로', positive: 48, negative: 37, theme: '2차전지·미국주식' },
  { name: '뽐뿌 증권포럼', status: 'enabled', lastCollected: '09:58', skipReason: '정상', surge: 'NAVER', positive: 36, negative: 42, theme: '플랫폼·배당' },
  { name: '에펨코리아 주식', status: 'public-demo-only', lastCollected: '10:05', skipReason: '인기글 링크 우선', surge: '두산로보틱스', positive: 61, negative: 18, theme: '로봇·AI' },
  { name: '토스증권 커뮤니티', status: 'public-demo-only', lastCollected: '10:02', skipReason: '제목 링크만', surge: '한미반도체', positive: 57, negative: 22, theme: '장비·실적' },
  { name: '블라인드 주식 라운지', status: 'local-research-only', lastCollected: '09:54', skipReason: '요약 통계만', surge: 'SOXS', positive: 28, negative: 51, theme: '해외주식·변동성' }
];

const humanStats = [
  { label: '수집 소스', value: '4개', meta: 'enabled 1 · demo 2' },
  { label: '급증 종목', value: '6개', meta: '상위 N% 기준' },
  { label: '인기글 후보', value: '18건', meta: '원문 링크만' },
  { label: '테마', value: '5개', meta: '반도체·2차전지' },
  { label: '주의 소스', value: '2개', meta: 'skip 사유 있음' }
];

const surgeStocks = [
  { stock: '삼성전자', community: '네이버 종토방', delta: '+34%', tone: '긍정 우세' },
  { stock: '두산로보틱스', community: '에펨코리아', delta: '+29%', tone: '긍정 우세' },
  { stock: '에코프로', community: '디시 주식', delta: '+24%', tone: '혼재' },
  { stock: '한미반도체', community: '토스증권', delta: '+22%', tone: '긍정 우세' },
  { stock: 'NAVER', community: '뽐뿌 증권포럼', delta: '+18%', tone: '부정 증가' },
  { stock: 'SOXS', community: '블라인드', delta: '+13%', tone: '부정 우세' }
];

const sourceStates = [
  { status: 'enabled', count: 1, note: '정상 수집' },
  { status: 'public-demo-only', count: 2, note: '공개 화면 기준' },
  { status: 'local-research-only', count: 1, note: '로컬 연구용' },
  { status: 'disabled', count: 0, note: '현재 없음' }
];

const themeRows = [
  { theme: '반도체', naver: 42, dc: 31, ppomppu: 18, fmkorea: 29, leader: '네이버 종토방' },
  { theme: '2차전지', naver: 16, dc: 38, ppomppu: 21, fmkorea: 14, leader: '디시 주식' },
  { theme: '로봇·AI', naver: 18, dc: 20, ppomppu: 11, fmkorea: 44, leader: '에펨코리아' },
  { theme: '미국주식', naver: 8, dc: 35, ppomppu: 12, fmkorea: 18, leader: '디시 주식' },
  { theme: '배당·가치', naver: 21, dc: 8, ppomppu: 29, fmkorea: 9, leader: '뽐뿌 증권포럼' },
  { theme: '환율·금리', naver: 14, dc: 24, ppomppu: 18, fmkorea: 12, leader: '디시 주식' }
];

const topPosts = [
  { community: '네이버 종토방', stock: '삼성전자', rank: '상위 4%', signal: '조회수 급증' },
  { community: '에펨코리아', stock: '두산로보틱스', rank: '상위 2%', signal: '댓글 속도 증가' },
  { community: '디시 주식', stock: '에코프로', rank: '상위 6%', signal: '상위 반응 글 확산' },
  { community: '토스증권', stock: '한미반도체', rank: '상위 7%', signal: '관심 등록 증가' }
];

const experiments = [
  { community: '네이버 종토방', style: '반응 추종', returnPct: '+1.8%', hitRate: '53%', drawdown: '-4.2%' },
  { community: '디시 주식', style: '반응 역추적', returnPct: '+0.6%', hitRate: '49%', drawdown: '-5.1%' },
  { community: '에펨코리아', style: '급증 관찰', returnPct: '+2.4%', hitRate: '55%', drawdown: '-3.6%' },
  { community: '토스증권', style: '관심 등록 변화', returnPct: '+1.2%', hitRate: '51%', drawdown: '-3.9%' }
];

const agentPersonas = [
  { name: 'Momentum', label: '언급 급증 추적', returnPct: '+3.2%', winRate: '55%', drawdown: '-3.8%', trades: 18, status: 'active' },
  { name: 'Contrarian', label: '과열 반대 관찰', returnPct: '+1.1%', winRate: '49%', drawdown: '-5.4%', trades: 12, status: 'watch' },
  { name: 'Risk Guard', label: '신뢰도 낮으면 스킵', returnPct: '+0.8%', winRate: '58%', drawdown: '-2.1%', trades: 8, status: 'guard' },
  { name: 'Community Follow', label: '인기글 상위권 추적', returnPct: '+2.4%', winRate: '53%', drawdown: '-4.0%', trades: 21, status: 'active' }
];

const agentPipeline = [
  { step: '입력 수집', count: 42, detail: '커뮤니티·가격 snapshot' },
  { step: '신뢰도 배점', count: 31, detail: '편중·stale·원문 확인' },
  { step: '판단 key', count: 14, detail: '중복 판단 방지' },
  { step: 'paper 후보', count: 3, detail: '실거래 아님' }
];

const agentDecisionLogs = [
  { time: '10:02', agent: 'Momentum', stock: '삼성전자', action: '관찰 유지', input: '반응 +18p · 가격 +1.2%', state: '판단 생성', key: 'mom-v3-005930-1002' },
  { time: '09:48', agent: 'Risk Guard', stock: 'NAVER', action: '스킵', input: '부정 +14p · 출처 편중 58%', state: '스킵 사유', key: 'risk-v2-035420-0948' },
  { time: '09:35', agent: 'Community Follow', stock: '두산로보틱스', action: 'paper 후보', input: '상위 2% 글 · 가격 변동', state: '후보 기록', key: 'follow-v1-454910-0935' },
  { time: '09:20', agent: 'Contrarian', stock: '에코프로', action: '관찰만', input: '관심 +24% · 가격 -1.1%', state: '판단 생성', key: 'contra-v2-086520-0920' }
];

const strategyVersions = [
  { version: 'mom-v3', persona: 'Momentum', rule: '언급 증가 + 가격 지지 + 출처 3개 이상', keys: 6 },
  { version: 'risk-v2', persona: 'Risk Guard', rule: '출처 편중 55% 이상이면 후보 제외', keys: 4 },
  { version: 'follow-v1', persona: 'Community Follow', rule: '인기글 상위 N%와 키워드 동시 관찰', keys: 7 },
  { version: 'contra-v2', persona: 'Contrarian', rule: '가격 하락과 관심 증가 괴리만 관찰', keys: 3 }
];
</script>

<template>
  <section class="surface-page communities-page terminal-density-page">
    <section class="terminal-board human-terminal" aria-labelledby="human-title">
      <div class="terminal-title-row">
        <div>
          <p class="label">human indicator</p>
          <h2 id="human-title">인간 지표</h2>
          <span>커뮤니티별 반응, 수집 상태, 내부 상위권 글을 한 번에 비교합니다.</span>
        </div>
        <span class="status-pill subtle">커뮤니티 반응 비교</span>
      </div>

      <nav class="human-view-tabs" aria-label="인간 지표 하위 화면">
        <RouterLink
          v-for="tab in humanViewTabs"
          :key="tab.view"
          :class="{ active: activeHumanView === tab.view }"
          :to="tab.to"
        >
          {{ tab.label }}
        </RouterLink>
      </nav>

      <div class="terminal-kpi-row" aria-label="인간 지표 요약">
        <article v-for="item in humanStats" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <em>{{ item.meta }}</em>
        </article>
      </div>

      <section class="human-workbench">
        <div class="human-source-table">
          <div class="table-caption">
            <div>
              <p class="label">source matrix</p>
              <h3>커뮤니티별 언급 급증과 반응 비율</h3>
            </div>
            <span class="status-pill warning">성과 해석 주의</span>
          </div>
          <div class="human-table-head">
            <span>커뮤니티</span>
            <span>급증 종목</span>
            <span>긍정/부정</span>
            <span>수집 상태</span>
            <span>관심 테마</span>
          </div>
          <article v-for="community in communities" :key="community.name">
            <div class="community-name-cell">
              <strong>{{ community.name }}</strong>
              <span>{{ community.status }}</span>
            </div>
            <div>
              <strong>{{ community.surge }}</strong>
              <small>{{ community.skipReason }}</small>
            </div>
            <div class="community-ratio-cell">
              <div class="ratio-track">
                <i class="positive" :style="{ width: `${community.positive}%` }"></i>
                <i class="negative" :style="{ width: `${community.negative}%` }"></i>
                <i class="neutral" :style="{ width: `${100 - community.positive - community.negative}%` }"></i>
              </div>
              <small>긍정 {{ community.positive }} · 부정 {{ community.negative }}</small>
            </div>
            <div>
              <strong>{{ community.lastCollected }}</strong>
              <small>{{ community.status }}</small>
            </div>
            <strong>{{ community.theme }}</strong>
          </article>
        </div>

        <aside class="human-side-rail">
          <section>
            <p class="label">surge board</p>
            <h3>커뮤니티별 언급 급증 종목</h3>
            <article v-for="(stock, index) in surgeStocks" :key="`${stock.stock}-${stock.community}`">
              <b>{{ index + 1 }}</b>
              <div>
                <strong>{{ stock.stock }}</strong>
                <span>{{ stock.community }} · {{ stock.tone }}</span>
              </div>
              <em>{{ stock.delta }}</em>
            </article>
          </section>
          <section>
            <p class="label">source state</p>
            <h3>수집 상태</h3>
            <div class="policy-grid">
              <span v-for="state in sourceStates" :key="state.status">
                <strong>{{ state.count }}</strong>
                {{ state.status }}
              </span>
            </div>
          </section>
        </aside>
      </section>

      <section class="human-theme-table" aria-label="커뮤니티별 관심 테마">
        <div class="table-caption">
          <div>
            <p class="label">theme map</p>
            <h3>커뮤니티별 관심 테마</h3>
          </div>
        </div>
        <div class="theme-row theme-head">
          <span>테마</span><span>네이버</span><span>디시</span><span>뽐뿌</span><span>에펨</span><span>강한 곳</span>
        </div>
        <div v-for="theme in themeRows" :key="theme.theme" class="theme-row">
          <strong>{{ theme.theme }}</strong>
          <span>{{ theme.naver }}</span>
          <span>{{ theme.dc }}</span>
          <span>{{ theme.ppomppu }}</span>
          <span>{{ theme.fmkorea }}</span>
          <em>{{ theme.leader }}</em>
        </div>
      </section>

      <section class="human-bottom-strip">
        <div>
          <p class="label">top layer</p>
          <h3>인기글·개념글 레이어</h3>
          <article v-for="post in topPosts" :key="`${post.community}-${post.stock}`">
            <span>{{ post.community }}</span>
            <strong>{{ post.stock }}</strong>
            <em>{{ post.rank }} · {{ post.signal }}</em>
          </article>
        </div>
        <div>
          <p class="label">paper experiment</p>
          <h3>커뮤니티별 성과 실험</h3>
          <article v-for="experiment in experiments" :key="`${experiment.community}-${experiment.style}`">
            <span>{{ experiment.style }}</span>
            <strong>{{ experiment.community }}</strong>
            <em>{{ experiment.returnPct }} · 적중률 {{ experiment.hitRate }} · 최대 낙폭 {{ experiment.drawdown }}</em>
          </article>
        </div>
      </section>

      <section id="agent-simulation" class="human-agent-section" aria-labelledby="human-agent-title">
        <div class="table-caption">
          <div>
            <p class="label">agent simulation</p>
            <h3 id="human-agent-title">모의 에이전트 판단 기록</h3>
          </div>
          <span class="status-pill warning">인간 지표 기반 · 실거래 아님</span>
        </div>

        <section class="agent-ledger-layout">
          <div class="agent-leaderboard">
            <div class="table-caption">
              <div>
                <p class="label">paper leaderboard</p>
                <h3>페르소나별 모의 성과</h3>
              </div>
            </div>
            <article v-for="persona in agentPersonas" :key="persona.name">
              <span :class="['agent-state-dot', persona.status]"></span>
              <div>
                <strong>{{ persona.name }}</strong>
                <small>{{ persona.label }}</small>
              </div>
              <em>{{ persona.returnPct }}</em>
              <span>승률 {{ persona.winRate }}</span>
              <span>낙폭 {{ persona.drawdown }}</span>
              <span>{{ persona.trades }}회</span>
            </article>
          </div>

          <aside class="agent-pipeline">
            <div>
              <p class="label">input pipeline</p>
              <h3>판단 입력값</h3>
            </div>
            <article v-for="item in agentPipeline" :key="item.step">
              <strong>{{ item.count }}</strong>
              <span>{{ item.step }}</span>
              <em>{{ item.detail }}</em>
            </article>
          </aside>
        </section>

        <section class="agent-log-terminal">
          <div class="table-caption">
            <div>
              <p class="label">decision log</p>
              <h3>최근 판단 로그</h3>
            </div>
            <span class="status-pill subtle">판단 key로 중복 방지</span>
          </div>
          <div class="agent-log-head">
            <span>시간</span><span>종목</span><span>에이전트</span><span>상태</span><span>입력값</span><span>판단 key</span>
          </div>
          <article v-for="log in agentDecisionLogs" :key="log.key">
            <time>{{ log.time }}</time>
            <strong>{{ log.stock }}</strong>
            <span>{{ log.agent }} · {{ log.action }}</span>
            <em>{{ log.state }}</em>
            <span>{{ log.input }}</span>
            <code>{{ log.key }}</code>
          </article>
        </section>

        <section class="strategy-version-table">
          <div class="table-caption">
            <div>
              <p class="label">strategy versions</p>
              <h3>전략 버전과 판단 key 기준</h3>
            </div>
            <span class="status-pill subtle">모의 판단 기록</span>
          </div>
          <article v-for="strategy in strategyVersions" :key="strategy.version">
            <strong>{{ strategy.version }}</strong>
            <span>{{ strategy.persona }}</span>
            <em>{{ strategy.rule }}</em>
            <b>{{ strategy.keys }} keys</b>
          </article>
        </section>
      </section>
    </section>
  </section>
</template>
