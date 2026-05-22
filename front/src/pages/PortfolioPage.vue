<script setup lang="ts">
type HoldingTone = 'up' | 'down' | 'flat';
type OrderState = '체결 mock' | '주문 후보' | '관찰' | '스킵' | '취소';

const summary = [
  { label: '가상 예수금', value: '5,420,000원', meta: '실거래 아님', tone: 'flat' },
  { label: '평가금액', value: '14,860,000원', meta: 'mock snapshot', tone: 'flat' },
  { label: '총 손익', value: '+280,000원', meta: '+1.92%', tone: 'up' },
  { label: '30일 수익률', value: '+2.4%', meta: 'paper 기준', tone: 'up' },
  { label: 'OCR 후보', value: '7건', meta: '확인 필요', tone: 'flat' },
  { label: '미확인 원문', value: '3건', meta: '마스킹 대기', tone: 'down' }
];

const allocation = [
  { label: '반도체', value: '42%', tone: 'up' },
  { label: '플랫폼', value: '18%', tone: 'down' },
  { label: '로봇', value: '16%', tone: 'up' },
  { label: 'ETF', value: '14%', tone: 'flat' },
  { label: '현금', value: '10%', tone: 'flat' }
];

const holdings: {
  name: string;
  qty: string;
  average: string;
  current: string;
  pnl: string;
  reaction: string;
  agent: string;
  tone: HoldingTone;
}[] = [
  { name: '삼성전자', qty: '80주', average: '76,900원', current: '78,200원', pnl: '+104,000원', reaction: '반도체 긍정 +18p', agent: '모멘텀 관찰', tone: 'up' },
  { name: 'NAVER', qty: '30주', average: '184,000원', current: '182,600원', pnl: '-42,000원', reaction: '비용 우려 +14p', agent: '리스크 회피', tone: 'down' },
  { name: '두산로보틱스', qty: '20주', average: '126,200원', current: '132,100원', pnl: '+118,000원', reaction: '인기글 상위권', agent: '커뮤니티 추종', tone: 'up' },
  { name: '한미반도체', qty: '12주', average: '168,000원', current: '171,500원', pnl: '+42,000원', reaction: '장비 수주 언급', agent: '뉴스 연결', tone: 'up' },
  { name: 'SOXS', qty: '35주', average: '13,540원', current: '13,769원', pnl: '+8,015원', reaction: '부정·변동성 글', agent: '검증 대기', tone: 'flat' }
];

const orders: { time: string; stock: string; state: OrderState; amount: string; reason: string }[] = [
  { time: '09:35', stock: '두산로보틱스', state: '체결 mock', amount: '20주', reason: '언급 급증과 가격 snapshot 동시 확인' },
  { time: '09:48', stock: 'NAVER', state: '스킵', amount: '-', reason: '출처 다양성 낮음' },
  { time: '10:02', stock: '삼성전자', state: '주문 후보', amount: '10주', reason: '반응 방향과 거래량이 같은 방향' },
  { time: '10:07', stock: '한미반도체', state: '관찰', amount: '-', reason: '공시 원문 확인 필요' },
  { time: '10:11', stock: 'SOXS', state: '스킵', amount: '-', reason: 'mock 가격 비중 높음' }
];

const ledger = [
  { type: '현금 변동', detail: '두산로보틱스 체결 mock', value: '-2,642,000원' },
  { type: '수수료 mock', detail: '체결 비용 추정', value: '-1,320원' },
  { type: '포지션 갱신', detail: '두산로보틱스 20주 추가', value: '+20주' },
  { type: '현금 대기', detail: '삼성전자 주문 후보', value: '변동 없음' },
  { type: '검증 로그', detail: 'OCR 평균단가 대조', value: '2건 확인' }
];

const importPreview = [
  { source: '토스증권 OCR', stock: '삼성전자', qty: '80주', avg: '76,900원', confidence: 92 },
  { source: '키움 거래내역', stock: '두산로보틱스', qty: '20주', avg: '126,200원', confidence: 88 },
  { source: '미래에셋 CSV', stock: 'NAVER', qty: '30주', avg: '184,000원', confidence: 96 },
  { source: 'OCR 후보', stock: '한미반도체', qty: '?', avg: '확인 필요', confidence: 61 },
  { source: '수기 입력 후보', stock: 'SOXS', qty: '35주', avg: '13,540원', confidence: 74 }
];

const reviews = [
  { label: '체결 후 30분', value: '언급 +14%', note: '가격은 +1.2%로 천천히 따라옴', tone: 'up' },
  { label: '뉴스 반응', value: '2건 연결', note: '기사보다 커뮤니티 반응이 먼저 튐', tone: 'flat' },
  { label: '가격 지연', value: '15분', note: '현재가 판단에는 사용하지 않음', tone: 'down' },
  { label: '원문 확인', value: '3건 대기', note: '인기글 원문 링크 확인 필요', tone: 'flat' }
];
</script>

<template>
  <section class="surface-page portfolio-page portfolio-ledger-page">
    <section class="portfolio-command-hero" aria-labelledby="portfolio-title">
      <div>
        <p class="label">paper portfolio</p>
        <h2 id="portfolio-title">내 포트폴리오</h2>
        <span>가상 자산, OCR 후보, 주문·원장, 체결 후 반응을 한 화면에서 대조합니다.</span>
      </div>
      <div class="portfolio-hero-badges">
        <span class="status-pill warning">실거래 아님</span>
        <span class="status-pill">mock ledger</span>
      </div>
    </section>

    <section class="portfolio-kpi-strip portfolio-asset-grid" aria-label="포트폴리오 요약">
      <article v-for="item in summary" :key="item.label" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <em>{{ item.meta }}</em>
      </article>
    </section>

    <section class="portfolio-workbench">
      <article class="portfolio-holdings-panel">
        <div class="section-band-title">
          <div>
            <p class="label">holdings</p>
            <h3>보유 종목과 반응 연결</h3>
          </div>
          <RouterLink class="detail-link" :to="{ path: '/communities', query: { view: 'agents' } }">모의 판단 로그</RouterLink>
        </div>

        <div class="portfolio-holding-head">
          <span>종목</span>
          <span>수량</span>
          <span>평균</span>
          <span>현재</span>
          <span>손익</span>
          <span>반응</span>
          <span>연결</span>
        </div>
        <article v-for="holding in holdings" :key="holding.name" class="portfolio-holding-row">
          <strong>{{ holding.name }}</strong>
          <span>{{ holding.qty }}</span>
          <span>{{ holding.average }}</span>
          <span>{{ holding.current }}</span>
          <em :class="holding.tone">{{ holding.pnl }}</em>
          <span>{{ holding.reaction }}</span>
          <small>{{ holding.agent }}</small>
        </article>
      </article>

      <aside class="portfolio-sync-panel">
        <p class="label">asset sync</p>
        <h3>자산 OCR · 주식 계좌 연결 준비</h3>
        <p>업로드 파일은 아직 저장하지 않는 화면 설계입니다. 계좌번호, 이름, 주문번호는 연결 전 반드시 제외합니다.</p>
        <button type="button">이미지 선택 mock</button>
        <div class="portfolio-sync-rule">
          <span>민감정보 마스킹</span>
          <strong>필수</strong>
        </div>
        <div class="portfolio-sync-rule">
          <span>가상 원장 매핑</span>
          <strong>준비</strong>
        </div>
        <div class="allocation-stack" aria-label="자산 배분">
          <article v-for="item in allocation" :key="item.label" :class="item.tone">
            <span>{{ item.label }}</span>
            <i><mark :style="{ width: item.value }"></mark></i>
            <strong>{{ item.value }}</strong>
          </article>
        </div>
      </aside>
    </section>

    <section class="portfolio-dense-grid">
      <article class="portfolio-import-panel">
        <div class="section-band-title compact">
          <div>
            <p class="label">import preview</p>
            <h3>OCR/거래내역 후보</h3>
          </div>
          <span>확인 후 반영</span>
        </div>
        <article v-for="item in importPreview" :key="`${item.source}-${item.stock}`">
          <span>{{ item.source }}</span>
          <strong>{{ item.stock }}</strong>
          <em>{{ item.qty }} · {{ item.avg }}</em>
          <b>{{ item.confidence }}%</b>
        </article>
      </article>

      <article class="portfolio-orders-panel">
        <div class="section-band-title compact">
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
      </article>

      <article class="portfolio-ledger-panel">
        <div class="section-band-title compact">
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
      </article>
    </section>

    <section class="portfolio-review-strip" aria-label="체결 후 복기">
      <div>
        <p class="label">post-trade review</p>
        <h3>체결 후 복기</h3>
      </div>
      <article v-for="review in reviews" :key="review.label" :class="review.tone">
        <span>{{ review.label }}</span>
        <strong>{{ review.value }}</strong>
        <em>{{ review.note }}</em>
      </article>
    </section>
  </section>
</template>
