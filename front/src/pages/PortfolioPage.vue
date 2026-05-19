<script setup lang="ts">
const summary = [
  { label: '가상 예수금', value: '5,420,000원', meta: '실거래 아님' },
  { label: '평가금액', value: '14,860,000원', meta: 'mock' },
  { label: '총 손익', value: '+280,000원', meta: '+1.92%' },
  { label: '30일 수익률', value: '+2.4%', meta: '모의 원장' },
  { label: 'OCR 후보', value: '7건', meta: '확인 필요' },
  { label: '미확인 원문', value: '3건', meta: '제목 링크' }
];

const holdings = [
  { name: '삼성전자', qty: 80, average: '76,900원', current: '78,200원', pnl: '+104,000원', reaction: '반도체 긍정 반응 증가', agent: 'Momentum 관찰' },
  { name: 'NAVER', qty: 30, average: '184,000원', current: '182,600원', pnl: '-42,000원', reaction: '비용 우려 키워드 증가', agent: 'Risk Guard 스킵' },
  { name: '두산로보틱스', qty: 20, average: '126,200원', current: '132,100원', pnl: '+118,000원', reaction: '인기글 상위권 도달', agent: 'Community Follow 후보' },
  { name: '한미반도체', qty: 12, average: '168,000원', current: '171,500원', pnl: '+42,000원', reaction: '장비 수주 키워드 증가', agent: 'News Linker 관찰' },
  { name: 'SOXS', qty: 35, average: '13,540원', current: '13,769원', pnl: '+8,015원', reaction: '부정 우세·변동성 글', agent: 'Freshness Guard 스킵' }
];

const orders = [
  { time: '09:35', stock: '두산로보틱스', state: '체결 mock', amount: '20주', reason: '커뮤니티 반응 급증 관찰' },
  { time: '09:48', stock: 'NAVER', state: '스킵', amount: '-', reason: '출처 다양성 낮음' },
  { time: '10:02', stock: '삼성전자', state: '주문 후보', amount: '10주', reason: '반응과 가격 snapshot 동시 확인' },
  { time: '10:07', stock: '한미반도체', state: '관찰', amount: '-', reason: '공시 원문 확인 필요' },
  { time: '10:11', stock: 'SOXS', state: '스킵', amount: '-', reason: 'mock 가격 비중 높음' }
];

const ledger = [
  { type: '현금 변동', detail: '두산로보틱스 체결 mock', value: '-2,642,000원' },
  { type: '수수료 mock', detail: '체결 비용 추정', value: '-1,320원' },
  { type: '포지션 갱신', detail: '두산로보틱스 20주 추가', value: '+20주' },
  { type: '현금 변동', detail: '삼성전자 후보 대기', value: '변동 없음' },
  { type: '검증 로그', detail: 'OCR 평균단가 대조', value: '2건 확인' }
];

const importPreview = [
  { source: '토스증권 OCR', stock: '삼성전자', qty: '80주', avg: '76,900원', confidence: '92%' },
  { source: '키움 거래내역', stock: '두산로보틱스', qty: '20주', avg: '126,200원', confidence: '88%' },
  { source: '미래에셋 CSV', stock: 'NAVER', qty: '30주', avg: '184,000원', confidence: '96%' },
  { source: 'OCR 후보', stock: '한미반도체', qty: '?', avg: '확인 필요', confidence: '61%' },
  { source: '수기 입력 후보', stock: 'SOXS', qty: '35주', avg: '13,540원', confidence: '74%' }
];

const reviews = [
  '체결 뒤 30분 동안 커뮤니티 언급은 +14%, 가격은 +1.2%로 움직였습니다.',
  '삼성전자 보유 구간은 뉴스보다 커뮤니티 키워드가 먼저 움직였습니다.',
  'NAVER는 가격 하락보다 부정 키워드 증가가 먼저 감지됐지만 표본 수가 작았습니다.',
  'SOXS는 가격 snapshot이 mock이라 원장 반영보다 검증 대기 상태로 남겼습니다.'
];
</script>

<template>
  <section class="surface-page portfolio-page ledger-density-page">
    <section class="portfolio-ledger-board" aria-labelledby="portfolio-title">
      <div class="terminal-title-row">
        <div>
          <p class="label">paper portfolio</p>
          <h2 id="portfolio-title">내 포트폴리오</h2>
          <span>가상 원장, OCR 후보, 체결 후 반응 복기를 한 화면에서 비교합니다.</span>
        </div>
        <span class="status-pill warning">실거래 아님</span>
      </div>

      <section class="portfolio-kpi-strip" aria-label="포트폴리오 요약">
        <article v-for="item in summary" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <em>{{ item.meta }}</em>
        </article>
      </section>

      <section class="portfolio-main-ledger">
        <div class="holdings-terminal">
          <div class="table-caption">
            <div>
              <p class="label">holdings</p>
              <h3>보유 종목과 반응 연결</h3>
            </div>
            <RouterLink class="detail-link" :to="{ path: '/communities', query: { view: 'agents' } }">모의 판단 보기 →</RouterLink>
          </div>
          <div class="holdings-head">
            <span>종목</span><span>수량</span><span>평균</span><span>현재</span><span>손익</span><span>반응</span><span>에이전트</span>
          </div>
          <article v-for="holding in holdings" :key="holding.name">
            <strong>{{ holding.name }}</strong>
            <span>{{ holding.qty }}주</span>
            <span>{{ holding.average }}</span>
            <span>{{ holding.current }}</span>
            <em>{{ holding.pnl }}</em>
            <span>{{ holding.reaction }}</span>
            <small>{{ holding.agent }}</small>
          </article>
        </div>

        <aside class="ocr-console">
          <p class="label">asset sync</p>
          <h3>자산 OCR · 주식 계좌 연결 준비</h3>
          <p>업로드 파일은 아직 저장하지 않는 화면 설계입니다. 계좌번호, 이름, 주문번호는 실제 연결 전에 제외해야 합니다.</p>
          <button type="button">이미지 선택 mock</button>
          <div>
            <span>민감정보 마스킹</span>
            <strong>필수</strong>
          </div>
          <div>
            <span>가상 원장 매핑</span>
            <strong>준비</strong>
          </div>
        </aside>
      </section>

      <section class="portfolio-subgrid">
        <div class="import-terminal">
          <div class="table-caption">
            <div>
              <p class="label">import preview</p>
              <h3>OCR/거래내역 후보</h3>
            </div>
            <span class="status-pill warning">확인 후 반영</span>
          </div>
          <article v-for="item in importPreview" :key="`${item.source}-${item.stock}`">
            <span>{{ item.source }}</span>
            <strong>{{ item.stock }}</strong>
            <em>{{ item.qty }} · {{ item.avg }}</em>
            <b>{{ item.confidence }}</b>
          </article>
        </div>

        <div class="orders-terminal">
          <div class="table-caption">
            <div>
              <p class="label">orders</p>
              <h3>주문 내역</h3>
            </div>
          </div>
          <article v-for="order in orders" :key="`${order.time}-${order.stock}`">
            <time>{{ order.time }}</time>
            <strong>{{ order.stock }} {{ order.amount }}</strong>
            <span>{{ order.state }}</span>
            <em>{{ order.reason }}</em>
          </article>
        </div>

        <div class="ledger-terminal">
          <div class="table-caption">
            <div>
              <p class="label">ledger</p>
              <h3>원장 내역</h3>
            </div>
          </div>
          <article v-for="entry in ledger" :key="`${entry.type}-${entry.detail}`">
            <span>{{ entry.type }}</span>
            <strong>{{ entry.detail }}</strong>
            <em>{{ entry.value }}</em>
          </article>
        </div>
      </section>

      <section class="post-review-line">
        <p class="label">post-trade review</p>
        <h3>체결 후 복기</h3>
        <ul>
          <li v-for="review in reviews" :key="review">{{ review }}</li>
        </ul>
      </section>
    </section>
  </section>
</template>
