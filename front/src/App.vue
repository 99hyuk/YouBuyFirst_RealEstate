<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';

const railItems = [
  { id: 'watch', label: '관심', shortcut: 'W' },
  { id: 'pulse', label: '관심도', shortcut: 'P' },
  { id: 'recent', label: '최근 본', shortcut: 'R' },
  { id: 'live', label: '실시간', shortcut: 'L' }
];

const liveTopics = [
  '속보 09:20 KOSDAQ 반등 구간에서 2차전지 언급 증가',
  '속보 09:35 삼성전자 반도체 키워드 30분 전 대비 +18%',
  '공시 10:00 두산로보틱스 단일가 변동성 확대',
  '커뮤니티 10:05 에코프로 인기글 상위 3% 도달'
];

const watchStocks = [
  { name: '삼성전자', symbol: '005930', value: '78,200원', change: '+1.24%', tone: 'up' },
  { name: '두산로보틱스', symbol: '454910', value: '132,100원', change: '+4.80%', tone: 'up' },
  { name: 'NAVER', symbol: '035420', value: '182,600원', change: '-0.70%', tone: 'down' },
  { name: '에코프로', symbol: '086520', value: '128,600원', change: '-1.96%', tone: 'down' }
];

const activeRailItem = ref('watch');
const railExpanded = ref(false);
const newsroomMenuDismissed = ref(false);
const route = useRoute();
const activeRailLabel = computed(() => railItems.find((item) => item.id === activeRailItem.value)?.label ?? '관심');
const newsroomFeeds = [
  { label: '뉴스', feed: 'news' },
  { label: '리포트', feed: 'reports' },
  { label: '영상', feed: 'videos' },
  { label: '블로그·커뮤니티', feed: 'links' }
];
const activeNewsroomFeed = computed(() => {
  if (route.path !== '/newsroom') return '';
  const feed = route.query.feed;
  return Array.isArray(feed) ? feed[0] ?? '' : feed ?? '';
});

const openRail = (id: string) => {
  activeRailItem.value = id;
  railExpanded.value = true;
};

const dismissNewsroomMenu = () => {
  newsroomMenuDismissed.value = true;
  window.setTimeout(() => {
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
  }, 0);
};
</script>

<template>
  <div :class="['app-shell', { 'edge-panel-open': railExpanded }]">
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
          <span
            :class="['nav-menu-parent', { 'menu-dismissed': newsroomMenuDismissed }]"
            @pointerenter="newsroomMenuDismissed = false"
            @pointerleave="newsroomMenuDismissed = false"
            @focusin="newsroomMenuDismissed = false"
          >
            <RouterLink data-testid="nav-newsroom" to="/newsroom" @click="dismissNewsroomMenu">뉴스룸</RouterLink>
            <span class="nav-submenu" aria-label="뉴스룸 하위 피드">
              <RouterLink
                v-for="feed in newsroomFeeds"
                :key="feed.feed"
                :class="{ active: activeNewsroomFeed === feed.feed }"
                :to="{ path: '/newsroom', query: { feed: feed.feed } }"
                @click="dismissNewsroomMenu"
              >
                {{ feed.label }}
              </RouterLink>
            </span>
          </span>
          <RouterLink data-testid="nav-stock" to="/stocks">종목</RouterLink>
          <RouterLink data-testid="nav-communities" to="/communities">인간 지표</RouterLink>
          <RouterLink data-testid="nav-indicators" to="/indicators">주요 지표</RouterLink>
          <RouterLink data-testid="nav-portfolio" to="/portfolio">내 포트폴리오</RouterLink>
        </nav>

        <div class="topbar-status topbar-actions" aria-label="서비스 상태와 계정">
          <span>KST</span>
          <button class="login-button" type="button">로그인</button>
          <span>참고용</span>
        </div>
      </div>

      <div class="topbar-ticker">
        <section class="live-ticker" aria-label="상단 실시간 속보">
          <div class="live-ticker-track">
            <span class="live-dot">속보</span>
            <span v-for="topic in liveTopics" :key="topic" class="ticker-topic">
              <strong>LIVE</strong>
              {{ topic }}
            </span>
            <span class="ticker-edge-test">mock data · 실시간 수집 전 API 계약 후보</span>
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
            <h2 id="site-footer-title">너나사<span>YouBuyFirst</span></h2>
            <p>
              커뮤니티 반응, 종목별 언급량, 시세 상태, 모의투자 에이전트를 함께 보는 투자 참고 실험 서비스입니다.
              실제 거래 지시나 개인화 투자 권유를 제공하지 않습니다.
            </p>
            <a href="mailto:yh99cho1@gmail.com">문의 yh99cho1@gmail.com</a>
          </section>

          <section class="footer-column" aria-labelledby="footer-features-title">
            <h3 id="footer-features-title">서비스 특징</h3>
            <span>관심종목 반응 변화 브리핑</span>
            <span>뉴스·공시·커뮤니티·가격 이벤트 연결</span>
            <span>커뮤니티별 반응 비교와 모의 성과 실험</span>
            <span>AI 에이전트 모의 판단 기록</span>
          </section>

          <section class="footer-column footer-legal" aria-labelledby="footer-notice-title">
            <h3 id="footer-notice-title">유의사항</h3>
            <p>
              모든 가격, 등락률, 수익률, 반응 지표는 참고용 추정치이며 공식 발표 값과 다를 수 있습니다.
              본 사이트는 정보 제공과 모의 실험 목적으로만 운영됩니다.
            </p>
            <p>
              어떠한 종목 거래도 권유하지 않으며, 이용으로 발생한 직·간접 손실에 대해 책임지지 않습니다.
            </p>
          </section>

          <section class="footer-column" aria-labelledby="footer-source-title">
            <h3 id="footer-source-title">데이터 출처</h3>
            <span>KRX · 네이버 금융</span>
            <span>Yahoo Finance · NASDAQ Trader</span>
            <span>업비트 · 공개 커뮤니티 게시글</span>
            <span>비공개·유료 데이터 미사용</span>
          </section>
        </div>

        <div class="site-footer-bottom">
          <span>© 2026 YouBuyFirst · 모든 시세는 비공식이며 실시간이 아닐 수 있습니다.</span>
          <span>BETA · mock wireframe · 2026.05</span>
        </div>
      </div>
    </footer>

    <aside :class="['edge-panel', { open: railExpanded }]" aria-label="오른쪽 확장 패널">
      <section class="edge-panel-screen">
        <div class="edge-panel-header">
          <div>
            <p class="label">quick panel</p>
            <h2>{{ activeRailLabel }}</h2>
          </div>
          <span class="panel-mini-badge">mock</span>
        </div>

        <div v-if="activeRailItem === 'watch'" class="edge-watch-list">
          <article v-for="stock in watchStocks" :key="stock.symbol" class="edge-watch-row">
            <span class="edge-symbol">{{ stock.name.slice(0, 1) }}</span>
            <div>
              <strong>{{ stock.name }}</strong>
              <p>{{ stock.symbol }}</p>
            </div>
            <div class="edge-price">
              <strong>{{ stock.value }}</strong>
              <em :class="stock.tone">{{ stock.change }}</em>
            </div>
          </article>
        </div>

        <div v-else-if="activeRailItem === 'pulse'" class="edge-live-list">
          <article>
            <span>반응 변화</span>
            <strong>삼성전자</strong>
            <em class="up">+18%</em>
          </article>
          <article>
            <span>가격 괴리</span>
            <strong>NAVER</strong>
            <em class="down">부정 증가</em>
          </article>
          <article>
            <span>관심 테마</span>
            <strong>반도체</strong>
            <em class="up">상위권</em>
          </article>
        </div>

        <div v-else class="edge-empty-state">
          <strong>{{ activeRailLabel }} 패널</strong>
          <p>현재는 화면 구조 확인용 mock 영역입니다. 실제 데이터 연결 전까지 표시 항목만 고정합니다.</p>
        </div>
      </section>
    </aside>

    <aside class="edge-rail" aria-label="오른쪽 고정 탭">
      <button
        class="rail-expand"
        type="button"
        :aria-expanded="railExpanded"
        aria-label="오른쪽 패널 열고 닫기"
        @click="railExpanded = !railExpanded"
      >
        <span>{{ railExpanded ? '»' : '«' }}</span>
        <em>{{ railExpanded ? '닫기' : '열기' }}</em>
      </button>
      <button
        v-for="item in railItems"
        :key="item.id"
        type="button"
        :class="{ active: railExpanded && activeRailItem === item.id }"
        :aria-pressed="railExpanded && activeRailItem === item.id"
        @click="openRail(item.id)"
      >
        <span>{{ item.shortcut }}</span>
        <em>{{ item.label }}</em>
      </button>
      <button class="theme-toggle" type="button" aria-label="라이트 다크 모드 전환">
        <span>◐</span>
        <em>다크모드</em>
      </button>
    </aside>
  </div>
</template>
