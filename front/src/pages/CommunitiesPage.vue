<script setup lang="ts">
import communityOverview from '../fixtures/community-overview.json';
import communityPerformance from '../fixtures/community-performance.json';
</script>

<template>
  <section class="page-grid">
    <div class="page-heading span-2">
      <p class="eyebrow">Community comparison shell</p>
      <h2>커뮤니티 비교</h2>
      <p>소스별 반응과 성과 후보를 mock 데이터로 나눠 보는 화면입니다.</p>
    </div>

    <section class="panel span-2">
      <p class="label">source state</p>
      <h3>수집 소스 상태</h3>
      <div class="ranking-list">
        <article v-for="item in communityOverview.items" :key="item.source" class="ranking-row">
          <strong>{{ item.sourceLabel }}</strong>
          <span>{{ item.mentionCount }}건</span>
          <span class="status-pill">{{ item.sourceState }}</span>
        </article>
      </div>
    </section>

    <section class="panel span-2">
      <p class="label">mock performance</p>
      <h3>커뮤니티 성과 후보</h3>
      <div class="ranking-list">
        <article v-for="item in communityPerformance.items" :key="item.community" class="ranking-row">
          <strong>{{ item.communityLabel }}</strong>
          <span>{{ item.strategyLabel }}</span>
          <span>{{ item.averageForwardReturnPct }}%</span>
        </article>
      </div>
    </section>
  </section>
</template>
