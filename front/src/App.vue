<script setup lang="ts">
import { computed, ref } from 'vue';
import dashboardSummary from './fixtures/dashboard-summary.json';

const edgeItems = [
  { id: 'invest', icon: '◆', label: '내 투자' },
  { id: 'watch', icon: '♥', label: '관심' },
  { id: 'recent', icon: '◔', label: '최근 본' },
  { id: 'live', icon: '↯', label: '실시간' }
];

const activeEdgeItem = ref('watch');
const edgeExpanded = ref(false);
const topRiser = dashboardSummary.risingStars[0];
const watchItems = dashboardSummary.risingStars.slice(0, 8);
const activeEdgeTitle = computed(() => edgeItems.find((item) => item.id === activeEdgeItem.value)?.label ?? '관심');
const tickerEdgeTest = 'RAIL EDGE TEST · 오른쪽 탭 옆에서 시작';
const formatPct = (value: number) => `${value > 0 ? '+' : ''}${value}%`;
const topTickerTopics = [
  { type: '속보', text: `${topRiser.name} 커뮤니티 언급 ${formatPct(topRiser.mentionDeltaPct)}` },
  { type: '속보', text: '한미반도체 HBM 댓글 30분 새 급증' },
  { type: '속보', text: '나스닥 선물 변동성 확대에 해외주식 글 증가' },
  { type: '속보', text: '삼성전자 반도체 업황 키워드 동반 상승' },
  { type: '핫토픽', text: 'AI·수급·실적 확인 대기' }
];
</script>

<template>
  <div :class="['app-shell', { 'edge-panel-open': edgeExpanded }]">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand-lockup">
          <RouterLink class="brand-home" data-testid="app-title" to="/dashboard">
            <h1>너나사 <span>YouBuyFirst</span></h1>
          </RouterLink>
          <strong>MOCK</strong>
        </div>
        <nav class="main-nav" aria-label="주요 화면">
          <RouterLink data-testid="nav-dashboard" to="/dashboard">대시보드</RouterLink>
          <RouterLink data-testid="nav-stock" to="/stocks/005930">종목 상세</RouterLink>
          <RouterLink data-testid="nav-communities" to="/communities">커뮤니티</RouterLink>
          <RouterLink data-testid="nav-indicators" to="/indicators">주요 지표</RouterLink>
          <RouterLink data-testid="nav-agents" to="/agents">에이전트</RouterLink>
          <RouterLink data-testid="nav-portfolio" to="/portfolio">내 포트폴리오</RouterLink>
        </nav>
        <div class="topbar-status topbar-actions" aria-label="서비스 상태와 계정">
          <span>KST</span>
          <button class="login-button" type="button">로그인</button>
          <span>참고용</span>
        </div>
      </div>

      <div class="topbar-ticker">
        <section class="live-ticker" aria-label="상단 고정 mock 지표 슬라이드">
          <div class="live-ticker-track">
            <span class="live-dot">속보</span>
            <span v-for="topic in topTickerTopics" :key="`${topic.type}-${topic.text}`" class="ticker-topic">
              <strong>{{ topic.type }}</strong>
              {{ topic.text }}
            </span>
            <span v-for="indicator in dashboardSummary.marketIndicators.slice(0, 3)" :key="indicator.label">
              {{ indicator.label }} {{ indicator.value }} {{ formatPct(indicator.changePct) }}
            </span>
            <span class="ticker-edge-test">{{ tickerEdgeTest }}</span>
          </div>
        </section>
      </div>
    </header>

    <main class="page-frame">
      <RouterView />
    </main>

    <footer class="site-footer" aria-labelledby="site-footer-title">
      <div class="site-footer-inner">
        <div class="site-footer-grid">
          <section class="site-footer-brand">
            <h2 id="site-footer-title">너나사 <span>YouBuyFirst</span></h2>
            <p>커뮤니티 반응, 종목 언급량, 지연 시세, 모의투자 에이전트를 함께 보는 투자 참고형 실험 서비스입니다.</p>
            <a href="mailto:yh99cho1@gmail.com">문의 yh99cho1@gmail.com</a>
          </section>

          <section class="footer-column" aria-labelledby="footer-features-title">
            <h3 id="footer-features-title">서비스 특징</h3>
            <span>반응 흐름 대시보드</span>
            <span>종목별 언급량·반응 방향</span>
            <span>커뮤니티별 모의 성과 비교</span>
            <span>AI 에이전트 모의 판단 로그</span>
          </section>

          <section class="footer-column footer-legal" aria-labelledby="footer-notice-title">
            <h3 id="footer-notice-title">유의사항</h3>
            <p>
              모든 가격·등락률·수익률·커뮤니티 반응 지표는 참고용 추정치이며 공식 값과 다를 수 있습니다.
              본 사이트는 정보 제공·학습·모의 실험 목적으로만 운영되며 어떠한 종목 매매도 권유하지 않습니다.
            </p>
            <p>
              투자 판단의 단독 근거로 사용하지 마시고, 이용으로 발생한 직·간접 손실에 대해 본 사이트는 책임지지 않습니다.
            </p>
          </section>

          <section class="footer-column" aria-labelledby="footer-source-title">
            <h3 id="footer-source-title">데이터 출처</h3>
            <span>KRX · 네이버 금융</span>
            <span>Yahoo Finance · NASDAQ Trader</span>
            <span>업비트 · 공개 커뮤니티 게시판</span>
            <span>비공개·유료 데이터 미사용</span>
          </section>
        </div>

        <div class="site-footer-bottom">
          <span>© 2026 YouBuyFirst · 모든 시세는 비공식이며 실시간이 아닐 수 있습니다.</span>
          <span>BETA · mock wireframe · 2026.05</span>
        </div>
      </div>
    </footer>

    <aside :class="['edge-panel', { open: edgeExpanded }]" aria-label="오른쪽 확장 패널">
      <section v-if="activeEdgeItem === 'watch'" class="edge-panel-screen">
        <div class="edge-panel-header">
          <h2>관심</h2>
          <div class="currency-toggle" aria-label="통화 보기">
            <span>$</span>
            <strong>원</strong>
          </div>
        </div>
        <article class="edge-panel-notice">
          <span>✦ 토스증권 AI</span>
          <strong>{{ topRiser.name }} 언급 흐름이 가장 빠르게 바뀌고 있어요</strong>
          <em>›</em>
        </article>
        <div class="edge-panel-section-title">
          <h3>관심 주식 TOP 8</h3>
          <p>관심 그룹에 담아보세요</p>
        </div>
        <div class="edge-watch-list">
          <article v-for="item in watchItems" :key="item.symbol" class="edge-watch-row">
            <span class="edge-symbol">{{ item.name.slice(0, 1) }}</span>
            <div>
              <strong>{{ item.name }}</strong>
              <p>{{ item.symbol }}</p>
            </div>
            <div class="edge-price">
              <strong>{{ item.heatScore.toLocaleString() }}</strong>
              <em :class="item.mentionDeltaPct > 0 ? 'up' : 'down'">
                {{ formatPct(item.mentionDeltaPct) }}
              </em>
            </div>
            <button type="button" aria-label="관심 추가">♥</button>
          </article>
        </div>
        <button class="edge-add-button" type="button">＋ 추가하기</button>
      </section>

      <section v-else-if="activeEdgeItem === 'live'" class="edge-panel-screen">
        <div class="edge-panel-header">
          <h2>실시간</h2>
          <span class="panel-mini-badge">mock</span>
        </div>
        <div class="edge-live-list">
          <article v-for="indicator in dashboardSummary.marketIndicators" :key="indicator.label">
            <span>{{ indicator.label }}</span>
            <strong>{{ indicator.value }}</strong>
            <em :class="indicator.trend === 'down' ? 'down' : 'up'">{{ formatPct(indicator.changePct) }}</em>
          </article>
        </div>
      </section>

      <section v-else class="edge-panel-screen">
        <div class="edge-panel-header">
          <h2>{{ activeEdgeTitle }}</h2>
          <span class="panel-mini-badge">mock</span>
        </div>
        <div class="edge-empty-state">
          <strong>{{ activeEdgeTitle }} 화면</strong>
          <p>오른쪽 레일에서 탭을 바꾸면 이 영역의 내용이 전환됩니다.</p>
        </div>
      </section>
    </aside>

    <aside class="edge-rail" aria-label="오른쪽 고정 탭">
      <button
        class="rail-expand"
        type="button"
        :aria-expanded="edgeExpanded"
        aria-label="오른쪽 패널 펼치기"
        @click="edgeExpanded = !edgeExpanded"
      >
        <span>{{ edgeExpanded ? '»' : '«' }}</span>
        <em>{{ edgeExpanded ? '닫기' : '열기' }}</em>
      </button>
      <button
        v-for="item in edgeItems"
        :key="item.id"
        type="button"
        :class="{ active: edgeExpanded && activeEdgeItem === item.id }"
        :aria-pressed="edgeExpanded && activeEdgeItem === item.id"
        @click="activeEdgeItem = item.id; edgeExpanded = true"
      >
        <span>{{ item.icon }}</span>
        <em>{{ item.label }}</em>
      </button>
      <button class="theme-toggle" type="button" aria-label="라이트 다크 모드 전환">☼</button>
    </aside>
  </div>
</template>
