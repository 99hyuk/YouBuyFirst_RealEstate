<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">커뮤니티 반응 관찰형 투자 참고 서비스</p>
        <h1 data-testid="app-title">너나사 YouBuyFirst</h1>
      </div>
      <nav class="main-nav" aria-label="주요 화면">
        <RouterLink data-testid="nav-dashboard" to="/dashboard">대시보드</RouterLink>
        <RouterLink data-testid="nav-stock" to="/stocks/005930">종목 상세</RouterLink>
        <RouterLink data-testid="nav-communities" to="/communities">커뮤니티</RouterLink>
        <RouterLink data-testid="nav-agents" to="/agents">에이전트</RouterLink>
        <RouterLink data-testid="nav-portfolio" to="/portfolio">포트폴리오 준비 중</RouterLink>
      </nav>
    </header>

    <main class="page-frame">
      <RouterView />
    </main>
  </div>
</template>
