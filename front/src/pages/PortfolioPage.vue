<script setup lang="ts">
type WatchTone = 'up' | 'down' | 'flat';
type WatchState = '알림 후보' | '관찰' | '확인 필요' | '스킵';

const summary = [
  { label: '관심 지역', value: '12곳', meta: '생활권·단지군', tone: 'flat' },
  { label: '급증 알림', value: '4건', meta: '최근 1시간', tone: 'up' },
  { label: '전세 우려', value: '3곳', meta: '매물 체감 감소', tone: 'down' },
  { label: '실거래 stale', value: '5건', meta: '공개 지연', tone: 'down' },
  { label: '원문 후보', value: '27건', meta: '카페·블로그', tone: 'flat' },
  { label: '확인 대기', value: '6건', meta: '별칭 매핑 필요', tone: 'flat' }
];

const allocation = [
  { label: '서울 핵심지', value: '38%', tone: 'up' },
  { label: '경기 남부', value: '24%', tone: 'up' },
  { label: '인천·송도', value: '14%', tone: 'down' },
  { label: '지방 광역시', value: '12%', tone: 'flat' },
  { label: '전세 우려', value: '12%', tone: 'down' }
];

const watchRegions: {
  name: string;
  scope: string;
  index: string;
  status: string;
  issue: string;
  reaction: string;
  next: string;
  tone: WatchTone;
}[] = [
  { name: '마포구 아파트', scope: '서울', index: '+0.55%', status: '실거래 지연', issue: '전세·학군', reaction: '기대 49 / 우려 33', next: '전세 매물 원문 확인', tone: 'up' },
  { name: '동탄역권', scope: '경기', index: '+0.31%', status: 'stale', issue: 'GTX·입주', reaction: '기대 44 / 우려 39', next: '입주 물량 대조', tone: 'flat' },
  { name: '성수동 생활권', scope: '서울', index: '+0.66%', status: 'mock', issue: '상권·임대료', reaction: '언급 +86%', next: '상권 키워드 분리', tone: 'up' },
  { name: '송도국제도시', scope: '인천', index: '-0.18%', status: 'stale', issue: '공급·국제학교', reaction: '우려 36', next: '미분양 추이 확인', tone: 'down' },
  { name: '분당·판교', scope: '경기', index: '+0.51%', status: 'mock', issue: '일자리·재건축', reaction: '기대 58', next: '재건축 별칭 매핑', tone: 'up' }
];

const actions: { time: string; target: string; state: WatchState; amount: string; reason: string }[] = [
  { time: '09:35', target: '마포구 아파트', state: '알림 후보', amount: '전세', reason: '언급 급증과 전세 매물 감소 체감이 동시에 관찰됨' },
  { time: '09:48', target: '송도국제도시', state: '확인 필요', amount: '공급', reason: '공급 부담 언급이 많은데 실거래 표본이 늦음' },
  { time: '10:02', target: '성수동 생활권', state: '관찰', amount: '상권', reason: '상권·임대료 키워드가 블로그와 카페에 동시 확산' },
  { time: '10:07', target: '분당·판교', state: '관찰', amount: '재건축', reason: '일자리와 재건축 기대가 분리되어 움직임' },
  { time: '10:11', target: '동탄역권', state: '스킵', amount: 'GTX', reason: '입주 물량 우려와 교통 기대가 상쇄됨' }
];

const ledger = [
  { type: '관심 등록', detail: '마포구 아파트 전세 키워드 추가', value: '+1곳' },
  { type: '알림 조건', detail: '언급량 +30% 이상이면 표시', value: '활성' },
  { type: '별칭 매핑', detail: '공덕·마래푸·역세권 후보 연결', value: '3건' },
  { type: '데이터 대조', detail: '실거래 공개 지연 flag 유지', value: 'stale' },
  { type: '원문 확인', detail: '네이버 카페 댓글 묶음', value: '8건' }
];

const importPreview = [
  { source: '네이버 카페', target: '마포구 아파트', qty: '전세 18건', avg: '댓글 188', confidence: 86 },
  { source: '다음 카페', target: '동탄역권', qty: 'GTX 14건', avg: '입주 9건', confidence: 78 },
  { source: '지역 블로그', target: '성수동 생활권', qty: '상권 11건', avg: '임대료 7건', confidence: 81 },
  { source: '공공데이터 후보', target: '송도국제도시', qty: '미분양', avg: '확인 필요', confidence: 64 },
  { source: '수기 별칭 후보', target: '분당·판교', qty: '재건축', avg: '학군', confidence: 74 }
];

const reviews = [
  { label: '알림 후 30분', value: '언급 +14%', note: '가격보다 반응이 먼저 움직인 구간', tone: 'up' },
  { label: '공공데이터 대조', value: '2건 연결', note: '실거래 공개 지연을 별도 표기', tone: 'flat' },
  { label: '전세 우려', value: '3곳', note: '전세수급지수와 원문을 같이 확인', tone: 'down' },
  { label: '원문 확인', value: '6건 대기', note: '카페 별칭 DB 매핑 필요', tone: 'flat' }
];
</script>

<template>
  <section class="surface-page portfolio-page portfolio-ledger-page">
    <section class="portfolio-command-hero" aria-labelledby="portfolio-title">
      <div>
        <p class="label">watchlist ledger</p>
        <h2 id="portfolio-title">관심 지역</h2>
        <span>관심 지역, 원문 후보, 알림 조건, 공공데이터 대조 상태를 한 화면에서 관리합니다.</span>
      </div>
      <div class="portfolio-hero-badges">
        <span class="status-pill warning">부동산 자문 아님</span>
        <span class="status-pill">mock watchlist</span>
      </div>
    </section>

    <section class="portfolio-kpi-strip portfolio-asset-grid" aria-label="관심 지역 요약">
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
            <p class="label">watch targets</p>
            <h3>관심 지역과 반응 연결</h3>
          </div>
          <RouterLink class="detail-link" :to="{ path: '/realestate/reactions', query: { view: 'agents' } }">모의 판단 로그</RouterLink>
        </div>

        <div class="portfolio-holding-head">
          <span>지역/단지</span>
          <span>권역</span>
          <span>지표</span>
          <span>상태</span>
          <span>쟁점</span>
          <span>반응</span>
          <span>다음 확인</span>
        </div>
        <article v-for="region in watchRegions" :key="region.name" class="portfolio-holding-row">
          <strong>{{ region.name }}</strong>
          <span>{{ region.scope }}</span>
          <span>{{ region.index }}</span>
          <span>{{ region.status }}</span>
          <em :class="region.tone">{{ region.issue }}</em>
          <span>{{ region.reaction }}</span>
          <small>{{ region.next }}</small>
        </article>
      </article>

      <aside class="portfolio-sync-panel">
        <p class="label">source sync</p>
        <h3>커뮤니티 원문 · 별칭 DB 연결 준비</h3>
        <p>카페 글, 블로그, 공공데이터 후보는 아직 저장하지 않는 화면 설계입니다. 작성자, 연락처, 사적 정보는 연결 전 반드시 제외합니다.</p>
        <button type="button">원문 묶음 선택 mock</button>
        <div class="portfolio-sync-rule">
          <span>민감정보 마스킹</span>
          <strong>필수</strong>
        </div>
        <div class="portfolio-sync-rule">
          <span>지역 별칭 매핑</span>
          <strong>준비</strong>
        </div>
        <div class="allocation-stack" aria-label="관심 지역 분포">
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
            <p class="label">source preview</p>
            <h3>원문/공공데이터 후보</h3>
          </div>
          <span>확인 후 반영</span>
        </div>
        <article v-for="item in importPreview" :key="`${item.source}-${item.target}`">
          <span>{{ item.source }}</span>
          <strong>{{ item.target }}</strong>
          <em>{{ item.qty }} · {{ item.avg }}</em>
          <b>{{ item.confidence }}%</b>
        </article>
      </article>

      <article class="portfolio-orders-panel">
        <div class="section-band-title compact">
          <div>
            <p class="label">alerts</p>
            <h3>알림 판단 내역</h3>
          </div>
        </div>
        <article v-for="action in actions" :key="`${action.time}-${action.target}`">
          <time>{{ action.time }}</time>
          <strong>{{ action.target }} · {{ action.amount }}</strong>
          <span>{{ action.state }}</span>
          <em>{{ action.reason }}</em>
        </article>
      </article>

      <article class="portfolio-ledger-panel">
        <div class="section-band-title compact">
          <div>
            <p class="label">ledger</p>
            <h3>관찰 로그</h3>
          </div>
        </div>
        <article v-for="entry in ledger" :key="`${entry.type}-${entry.detail}`">
          <span>{{ entry.type }}</span>
          <strong>{{ entry.detail }}</strong>
          <em>{{ entry.value }}</em>
        </article>
      </article>
    </section>

    <section class="portfolio-review-strip" aria-label="알림 후 복기">
      <div>
        <p class="label">post-alert review</p>
        <h3>알림 후 복기</h3>
      </div>
      <article v-for="review in reviews" :key="review.label" :class="review.tone">
        <span>{{ review.label }}</span>
        <strong>{{ review.value }}</strong>
        <em>{{ review.note }}</em>
      </article>
    </section>
  </section>
</template>
