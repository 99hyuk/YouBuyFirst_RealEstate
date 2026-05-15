<script setup lang="ts">
import agentLeaderboard from '../fixtures/agent-leaderboard.json';
</script>

<template>
  <section class="page-grid">
    <div class="page-heading span-2">
      <p class="eyebrow">Agent leaderboard shell</p>
      <h2>에이전트 리더보드</h2>
      <p>AI 페르소나의 모의 성과를 관찰하는 자리이며, 투자 자문이나 수익 보장이 아닙니다.</p>
    </div>

    <section class="panel span-2">
      <p class="label">mock simulation</p>
      <h3>페르소나별 성과 후보</h3>
      <div class="ranking-list">
        <article v-for="agent in agentLeaderboard.items" :key="agent.agentId" class="ranking-row">
          <strong>{{ agent.name }}</strong>
          <span>{{ agent.persona }}</span>
          <span>{{ agent.returnPct }}%</span>
          <span class="status-pill">{{ agent.dataStatus }}</span>
        </article>
      </div>
    </section>
  </section>
</template>
