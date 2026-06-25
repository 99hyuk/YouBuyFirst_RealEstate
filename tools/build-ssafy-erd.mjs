import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const outHtml = resolve(root, 'docs/domains/realestate/SSAFY_ERD.html');
const outPdfHtml = resolve(root, 'output/pdf/ssafy-realestate-erd.html');

const tableRows = loadTableRows();
const latestFlyway = loadLatestFlyway();

const tables = {
  app_users: ['사용자 계정', 'PK id', 'username, email, display_name'],
  user_oauth_accounts: ['소셜 로그인', 'PK id', 'FK user_id'],
  user_watch_targets: ['관심 대상', 'PK id', 'FK user_id, L-FK target_id'],
  chat_messages: ['채팅 메시지', 'PK id', 'FK user_id nullable'],
  real_estate_targets: ['부동산 대상 정본', 'PK id', 'target_type, slug'],
  real_estate_regions: ['지역 프로필', 'PK/L-FK target_id', 'parent_region_id'],
  real_estate_complexes: ['단지 프로필', 'PK/L-FK target_id', 'region_target_id'],
  real_estate_complex_provider_keys: ['단지 외부키', 'PK id', 'complex_target_id'],
  real_estate_aliases: ['별칭 사전', 'PK id', 'target_id'],
  real_estate_target_edges: ['대상 관계', 'PK id', 'from_target_id, to_target_id'],
  real_estate_geocode: ['지오코딩 캐시', 'PK id', 'query_key'],
  real_estate_public_data_datasets: ['공공 데이터셋', 'PK dataset_id', 'provider'],
  real_estate_public_data_import_runs: ['수집 실행', 'PK id', 'run_key'],
  real_estate_public_data_raw_items: ['원천 raw', 'PK id', 'import_run_id'],
  real_estate_market_fact_staging: ['시장 사실 staging', 'PK id', 'raw_item_id'],
  real_estate_market_data_targets: ['수집 대상 지역', 'PK id', 'target_id'],
  real_estate_market_facts: ['시장 사실', 'PK id', 'target_id'],
  market_data_sources: ['공식 출처', 'PK id', 'provider'],
  market_data_schedules: ['데이터 일정', 'PK id', 'FK source_id'],
  map_boundary_assets: ['지도 경계 자산', 'PK id', 'asset_type'],
  map_features: ['지도 영역', 'PK id', 'boundary_asset_id, target_id'],
  map_layer_snapshots: ['지도 레이어 값', 'PK id', 'target_id'],
  real_estate_regional_reports: ['지역 분석 리포트', 'PK/FK target_id', 'report_id'],
  real_estate_regional_report_sources: ['리포트 근거 출처', 'PK id', 'FK report_target_id'],
  timeline_events: ['상세 타임라인', 'PK id', 'target_id'],
  evidence_logs: ['AI 근거 로그', 'PK id', 'target_id, snapshot_id'],
  evidence_log_items: ['근거 항목', 'PK id', 'FK evidence_log_id'],
  daily_briefings: ['데일리 브리핑', 'PK id', 'briefing_date'],
  daily_briefing_sections: ['브리핑 섹션', 'PK id', 'FK briefing_id'],
  daily_briefing_source_items: ['브리핑 출처', 'PK id', 'FK briefing_id'],
  crawl_targets: ['크롤링 대상', 'PK id', 'target_id'],
  crawl_runs: ['크롤링 실행', 'PK id', 'source, target_id'],
  community_posts: ['커뮤니티 게시글', 'PK id', 'source, external_id'],
  community_post_diffusion_events: ['확산 이벤트', 'PK id', 'post_id'],
  community_comment_collection_targets: ['댓글 수집 후보', 'PK id', 'post_id'],
  content_items: ['외부 콘텐츠', 'PK id', 'url_hash'],
  content_target_links: ['콘텐츠-대상 연결', 'PK content_item_id+target_id+link_type', 'target_id'],
  real_estate_reaction_snapshots: ['반응 스냅샷', 'PK id', 'target_id'],
  real_estate_reaction_snapshot_issues: ['반응 쟁점', 'PK id', 'snapshot_id'],
  policy_events: ['정책/공급 이벤트', 'PK id', 'event_type'],
  policy_event_targets: ['정책 영향 대상', 'PK policy_event_id+target_id+impact_type', 'target_id'],
};

const groups = [
  {
    title: '사용자, 인증, 채팅',
    color: '#ffe8ee',
    tables: ['app_users', 'user_oauth_accounts', 'user_watch_targets', 'chat_messages'],
  },
  {
    title: '부동산 대상 정본',
    color: '#fff1db',
    tables: [
      'real_estate_targets',
      'real_estate_regions',
      'real_estate_complexes',
      'real_estate_complex_provider_keys',
      'real_estate_aliases',
      'real_estate_target_edges',
      'real_estate_geocode',
    ],
  },
  {
    title: '공공데이터 수집과 시장 사실',
    color: '#e9f3ff',
    tables: [
      'real_estate_public_data_datasets',
      'real_estate_public_data_import_runs',
      'real_estate_public_data_raw_items',
      'real_estate_market_fact_staging',
      'real_estate_market_data_targets',
      'real_estate_market_facts',
      'market_data_sources',
      'market_data_schedules',
      'map_boundary_assets',
      'map_features',
      'map_layer_snapshots',
    ],
  },
  {
    title: '리포트, 타임라인, 근거',
    color: '#f1ebff',
    tables: [
      'real_estate_regional_reports',
      'real_estate_regional_report_sources',
      'timeline_events',
      'evidence_logs',
      'evidence_log_items',
      'daily_briefings',
      'daily_briefing_sections',
      'daily_briefing_source_items',
    ],
  },
  {
    title: '커뮤니티, 콘텐츠, 반응 보조',
    color: '#edf2f7',
    tables: [
      'crawl_targets',
      'crawl_runs',
      'community_posts',
      'community_post_diffusion_events',
      'community_comment_collection_targets',
      'content_items',
      'content_target_links',
      'real_estate_reaction_snapshots',
      'real_estate_reaction_snapshot_issues',
      'policy_events',
      'policy_event_targets',
    ],
  },
];

const relationRows = [
  ['real_estate_targets', '1:0..1', 'real_estate_regions', 'target_id', '지역 상세 profile'],
  ['real_estate_targets', '1:0..1', 'real_estate_complexes', 'target_id', '단지 상세 profile'],
  ['real_estate_regions', '1:N', 'real_estate_complexes', 'region_target_id', '단지가 대표 지역에 속함'],
  ['real_estate_targets', '1:N', 'real_estate_aliases', 'target_id', '검색/매칭 별칭'],
  ['real_estate_targets', 'N:M', 'real_estate_target_edges', 'from_target_id/to_target_id', '포함, 생활권, 영향권 graph'],
  ['real_estate_complexes', '1:N', 'real_estate_complex_provider_keys', 'complex_target_id', 'provider별 단지 외부키'],
  ['real_estate_public_data_import_runs', '1:N', 'real_estate_public_data_raw_items', 'import_run_id', '수집 실행별 raw landing'],
  ['real_estate_public_data_raw_items', '1:0..1', 'real_estate_market_fact_staging', 'raw_item_id', '검증/정제 중간 단계'],
  ['real_estate_targets', '1:N', 'real_estate_market_facts', 'target_id', '실거래, 전세, 가격지수 등 시장 사실'],
  ['market_data_sources', '1:N', 'market_data_schedules', 'source_id', '공식 출처별 공개 일정'],
  ['map_boundary_assets', '1:N', 'map_features', 'boundary_asset_id', '지도 경계 파일의 feature'],
  ['real_estate_targets', '1:N', 'map_features', 'target_id', '지도 geometry와 내부 target 매핑'],
  ['real_estate_targets', '1:N', 'map_layer_snapshots', 'target_id', '기간별 지도 heat 값'],
  ['real_estate_targets', '1:0..1', 'real_estate_regional_reports', 'target_id', '지역별 최신 리포트'],
  ['real_estate_regional_reports', '1:N', 'real_estate_regional_report_sources', 'report_target_id', '리포트 근거 출처'],
  ['real_estate_targets', '1:N', 'timeline_events', 'target_id', '상세 화면 시간축 캐시'],
  ['real_estate_targets', '1:N', 'evidence_logs', 'target_id', 'AI 평가 로그'],
  ['evidence_logs', '1:N', 'evidence_log_items', 'evidence_log_id', 'AI 평가가 인용한 근거 항목'],
  ['daily_briefings', '1:N', 'daily_briefing_sections', 'briefing_id', '브리핑 본문 섹션'],
  ['daily_briefings', '1:N', 'daily_briefing_source_items', 'briefing_id', '브리핑 출처'],
  ['app_users', '1:N', 'user_oauth_accounts', 'user_id', '소셜 로그인 계정 연결'],
  ['app_users', '1:N', 'user_watch_targets', 'user_id', '사용자별 관심 대상'],
  ['real_estate_targets', '1:N', 'user_watch_targets', 'target_id', '관심 지역/단지 대상'],
  ['app_users', '1:N', 'chat_messages', 'user_id', '로그인 채팅 작성자, 게스트는 nullable'],
  ['content_items', 'N:M', 'content_target_links', 'content_item_id/target_id', '뉴스/리포트와 target 연결'],
  ['real_estate_targets', '1:N', 'real_estate_reaction_snapshots', 'target_id', '기간별 반응 집계'],
  ['real_estate_reaction_snapshots', '1:N', 'real_estate_reaction_snapshot_issues', 'snapshot_id', '쟁점 비율'],
  ['policy_events', 'N:M', 'policy_event_targets', 'policy_event_id/target_id', '정책 영향 대상'],
];

const diagrams = [
  {
    title: '핵심 ERD 전체 관계도',
    lead: '가운데 real_estate_targets가 모든 지역/단지 식별자의 중심이고, 주변 기능은 target_id로 연결됩니다.',
    width: 1600,
    height: 830,
    groups: [
      ['사용자 기능', 40, 55, 250, 245, '#ffe8ee'],
      ['부동산 대상 정본', 475, 230, 420, 355, '#fff1db'],
      ['공공데이터 수집', 40, 600, 650, 185, '#e9f3ff'],
      ['시장/지도', 990, 110, 270, 270, '#e9f8ef'],
      ['리포트/근거', 1320, 170, 240, 420, '#f1ebff'],
      ['콘텐츠/반응 보조', 810, 620, 720, 170, '#edf2f7'],
    ],
    nodes: [
      n('app_users', 80, 105, 170, 68, 'user'),
      n('user_watch_targets', 80, 210, 170, 68, 'user'),
      n('real_estate_targets', 590, 350, 190, 86, 'target', ['PK id', 'target_type', 'slug']),
      n('real_estate_regions', 500, 260, 165, 62, 'target'),
      n('real_estate_complexes', 720, 260, 165, 62, 'target'),
      n('real_estate_aliases', 500, 480, 165, 62, 'target'),
      n('real_estate_target_edges', 720, 480, 165, 62, 'target'),
      n('real_estate_public_data_import_runs', 75, 660, 185, 62, 'ingest'),
      n('real_estate_public_data_raw_items', 300, 660, 185, 62, 'ingest'),
      n('real_estate_market_fact_staging', 525, 660, 185, 62, 'ingest'),
      n('real_estate_market_facts', 1015, 170, 200, 70, 'market'),
      n('map_layer_snapshots', 1015, 280, 200, 70, 'market'),
      n('real_estate_regional_reports', 1345, 230, 190, 68, 'report'),
      n('real_estate_regional_report_sources', 1345, 330, 190, 68, 'report'),
      n('evidence_logs', 1345, 430, 190, 68, 'report'),
      n('evidence_log_items', 1345, 530, 190, 68, 'report'),
      n('content_items', 850, 680, 170, 62, 'comm'),
      n('content_target_links', 1050, 680, 170, 62, 'comm'),
      n('real_estate_reaction_snapshots', 1250, 680, 190, 62, 'comm'),
    ],
    edges: [
      e('app_users', 'user_watch_targets', '1:N'),
      e('user_watch_targets', 'real_estate_targets', 'N:1'),
      e('real_estate_targets', 'real_estate_regions', '1:0..1'),
      e('real_estate_targets', 'real_estate_complexes', '1:0..1'),
      e('real_estate_targets', 'real_estate_aliases', '1:N'),
      e('real_estate_targets', 'real_estate_target_edges', 'N:M'),
      e('real_estate_public_data_import_runs', 'real_estate_public_data_raw_items', '1:N'),
      e('real_estate_public_data_raw_items', 'real_estate_market_fact_staging', '1:0..1'),
      e('real_estate_market_fact_staging', 'real_estate_market_facts', 'promote'),
      e('real_estate_targets', 'real_estate_market_facts', '1:N'),
      e('real_estate_targets', 'map_layer_snapshots', '1:N'),
      e('real_estate_targets', 'real_estate_regional_reports', '1:0..1'),
      e('real_estate_regional_reports', 'real_estate_regional_report_sources', '1:N', 'physical'),
      e('real_estate_targets', 'evidence_logs', '1:N'),
      e('evidence_logs', 'evidence_log_items', '1:N', 'physical'),
      e('content_items', 'content_target_links', '1:N'),
      e('content_target_links', 'real_estate_targets', 'N:1'),
      e('real_estate_targets', 'real_estate_reaction_snapshots', '1:N'),
    ],
  },
  {
    title: '부동산 대상 정본 상세 ERD',
    lead: '지역과 단지는 별도 독립 ID가 아니라 real_estate_targets.id를 확장합니다. 이 구조 덕분에 지도, 실거래, 리포트가 같은 target_id를 공유합니다.',
    width: 1500,
    height: 760,
    groups: [['target graph', 30, 55, 1440, 650, '#fff1db']],
    nodes: [
      n('real_estate_targets', 615, 285, 250, 92, 'target', ['PK id', 'target_type', 'display_name', 'slug']),
      n('real_estate_regions', 245, 130, 230, 86, 'target', ['PK/L-FK target_id', 'parent_region_id', 'legal_dong_code']),
      n('real_estate_complexes', 1015, 130, 230, 86, 'target', ['PK/L-FK target_id', 'region_target_id', 'coordinate_status']),
      n('real_estate_complex_provider_keys', 1015, 285, 230, 86, 'target', ['PK id', 'complex_target_id', 'provider_object_id']),
      n('real_estate_aliases', 245, 470, 230, 86, 'target', ['PK id', 'target_id', 'normalized_alias']),
      n('real_estate_target_edges', 615, 505, 250, 86, 'target', ['PK id', 'from_target_id', 'to_target_id', 'edge_type']),
      n('real_estate_geocode', 1015, 505, 230, 86, 'target', ['PK id', 'query_key', 'lat/lng']),
    ],
    edges: [
      e('real_estate_targets', 'real_estate_regions', '1:0..1'),
      e('real_estate_targets', 'real_estate_complexes', '1:0..1'),
      e('real_estate_regions', 'real_estate_regions', 'parent 1:N'),
      e('real_estate_regions', 'real_estate_complexes', '1:N'),
      e('real_estate_complexes', 'real_estate_complex_provider_keys', '1:N'),
      e('real_estate_targets', 'real_estate_aliases', '1:N'),
      e('real_estate_targets', 'real_estate_target_edges', 'N:M'),
    ],
  },
  {
    title: '공공데이터 수집에서 시장 사실까지',
    lead: '공식 데이터는 raw를 바로 화면에 쓰지 않고 수집 실행, 원천 row, staging 검증을 거쳐 market_facts로 승격됩니다.',
    width: 1500,
    height: 760,
    groups: [
      ['수집 pipeline', 30, 60, 1040, 300, '#e9f3ff'],
      ['화면 조회용 시장/지도', 1090, 60, 380, 590, '#e9f8ef'],
      ['공식 일정', 30, 405, 520, 245, '#fff6e6'],
    ],
    nodes: [
      n('real_estate_public_data_datasets', 75, 140, 210, 78, 'ingest', ['PK dataset_id', 'provider', 'source_url']),
      n('real_estate_public_data_import_runs', 325, 140, 210, 78, 'ingest', ['PK id', 'run_key', 'status']),
      n('real_estate_public_data_raw_items', 575, 140, 210, 78, 'ingest', ['PK id', 'import_run_id', 'raw_payload_json']),
      n('real_estate_market_fact_staging', 825, 140, 210, 78, 'ingest', ['PK id', 'raw_item_id', 'validation_status']),
      n('real_estate_market_data_targets', 425, 260, 230, 72, 'ingest', ['PK id', 'target_id', 'lawd_code']),
      n('real_estate_targets', 760, 430, 210, 82, 'target', ['PK id', 'target_type']),
      n('real_estate_market_facts', 1160, 155, 230, 86, 'market', ['PK id', 'target_id', 'fact_type', 'as_of/stale']),
      n('map_boundary_assets', 1135, 330, 210, 72, 'market', ['PK id', 'asset_type']),
      n('map_features', 1135, 450, 210, 72, 'market', ['PK id', 'boundary_asset_id', 'target_id']),
      n('map_layer_snapshots', 1135, 570, 210, 72, 'market', ['PK id', 'target_id', 'period_key']),
      n('market_data_sources', 95, 475, 190, 72, 'market', ['PK id', 'provider']),
      n('market_data_schedules', 325, 475, 190, 72, 'market', ['PK id', 'FK source_id']),
    ],
    edges: [
      e('real_estate_public_data_datasets', 'real_estate_public_data_import_runs', '1:N'),
      e('real_estate_public_data_import_runs', 'real_estate_public_data_raw_items', '1:N'),
      e('real_estate_public_data_raw_items', 'real_estate_market_fact_staging', '1:0..1'),
      e('real_estate_market_fact_staging', 'real_estate_market_facts', 'promote'),
      e('real_estate_market_data_targets', 'real_estate_targets', 'N:1'),
      e('real_estate_targets', 'real_estate_market_facts', '1:N'),
      e('map_boundary_assets', 'map_features', '1:N'),
      e('real_estate_targets', 'map_features', '1:N'),
      e('real_estate_targets', 'map_layer_snapshots', '1:N'),
      e('real_estate_market_facts', 'map_layer_snapshots', '계산 입력'),
      e('market_data_sources', 'market_data_schedules', '1:N', 'physical'),
    ],
  },
  {
    title: '리포트, 타임라인, 근거 ERD',
    lead: '지역 리포트는 본문만 저장하지 않고 출처와 근거 항목을 분리합니다. 사용자가 보는 설명과 검증 근거를 함께 남기는 구조입니다.',
    width: 1500,
    height: 760,
    groups: [
      ['지역 분석', 45, 80, 590, 500, '#f1ebff'],
      ['AI 근거 로그', 690, 80, 360, 500, '#f1ebff'],
      ['데일리 브리핑', 1090, 80, 360, 500, '#edf2f7'],
    ],
    nodes: [
      n('real_estate_targets', 95, 295, 190, 82, 'target', ['PK id', 'target_type']),
      n('real_estate_regional_reports', 365, 180, 220, 86, 'report', ['PK/FK target_id', 'report_id', 'body']),
      n('real_estate_regional_report_sources', 365, 380, 220, 86, 'report', ['PK id', 'FK report_target_id', 'url']),
      n('timeline_events', 365, 520, 220, 72, 'report', ['PK id', 'target_id', 'source_ref_id']),
      n('evidence_logs', 760, 210, 220, 86, 'report', ['PK id', 'target_id', 'summary']),
      n('evidence_log_items', 760, 410, 220, 86, 'report', ['PK id', 'FK evidence_log_id', 'ref_id']),
      n('daily_briefings', 1160, 170, 210, 78, 'report', ['PK id', 'briefing_date']),
      n('daily_briefing_sections', 1160, 325, 210, 78, 'report', ['PK id', 'FK briefing_id']),
      n('daily_briefing_source_items', 1160, 480, 210, 78, 'report', ['PK id', 'FK briefing_id']),
    ],
    edges: [
      e('real_estate_targets', 'real_estate_regional_reports', '1:0..1', 'physical'),
      e('real_estate_regional_reports', 'real_estate_regional_report_sources', '1:N', 'physical'),
      e('real_estate_targets', 'timeline_events', '1:N'),
      e('real_estate_targets', 'evidence_logs', '1:N'),
      e('evidence_logs', 'evidence_log_items', '1:N', 'physical'),
      e('daily_briefings', 'daily_briefing_sections', '1:N', 'physical'),
      e('daily_briefings', 'daily_briefing_source_items', '1:N', 'physical'),
    ],
  },
  {
    title: '사용자 기능과 커뮤니티 보조 ERD',
    lead: '사용자 저장/채팅은 app_users를 기준으로 하고, 공개 글과 콘텐츠는 부동산 판단의 정본이 아니라 target에 붙는 보조 관찰 근거입니다.',
    width: 1500,
    height: 760,
    groups: [
      ['사용자 기능', 40, 70, 430, 560, '#ffe8ee'],
      ['콘텐츠/반응 보조', 530, 70, 900, 560, '#edf2f7'],
    ],
    nodes: [
      n('app_users', 95, 150, 185, 78, 'user', ['PK id', 'username/email']),
      n('user_oauth_accounts', 310, 105, 185, 70, 'user', ['PK id', 'FK user_id']),
      n('user_watch_targets', 310, 235, 185, 70, 'user', ['PK id', 'FK user_id', 'target_id']),
      n('chat_messages', 310, 365, 185, 70, 'user', ['PK id', 'FK user_id nullable']),
      n('real_estate_targets', 630, 270, 200, 82, 'target', ['PK id', 'target_type']),
      n('crawl_targets', 575, 105, 180, 68, 'comm', ['PK id', 'source']),
      n('crawl_runs', 790, 105, 180, 68, 'comm', ['PK id', 'source']),
      n('community_posts', 1005, 105, 190, 68, 'comm', ['PK id', 'source/external_id']),
      n('community_post_diffusion_events', 1225, 95, 190, 68, 'comm', ['PK id', 'post_id']),
      n('community_comment_collection_targets', 1225, 205, 190, 68, 'comm', ['PK id', 'post_id']),
      n('content_items', 845, 430, 180, 68, 'comm', ['PK id', 'url_hash']),
      n('content_target_links', 1060, 430, 190, 68, 'comm', ['PK content+target+type']),
      n('real_estate_reaction_snapshots', 845, 555, 205, 68, 'comm', ['PK id', 'target_id']),
      n('real_estate_reaction_snapshot_issues', 1085, 555, 210, 68, 'comm', ['PK id', 'snapshot_id']),
      n('policy_events', 845, 270, 180, 68, 'comm', ['PK id', 'event_type']),
      n('policy_event_targets', 1060, 270, 190, 68, 'comm', ['PK event+target+impact']),
    ],
    edges: [
      e('app_users', 'user_oauth_accounts', '1:N', 'physical'),
      e('app_users', 'user_watch_targets', '1:N', 'physical'),
      e('app_users', 'chat_messages', '1:N', 'physical'),
      e('user_watch_targets', 'real_estate_targets', 'N:1'),
      e('crawl_targets', 'crawl_runs', '1:N'),
      e('crawl_runs', 'community_posts', '1:N'),
      e('community_posts', 'community_post_diffusion_events', '1:N'),
      e('community_posts', 'community_comment_collection_targets', '1:N'),
      e('content_items', 'content_target_links', '1:N'),
      e('content_target_links', 'real_estate_targets', 'N:1'),
      e('real_estate_targets', 'real_estate_reaction_snapshots', '1:N'),
      e('real_estate_reaction_snapshots', 'real_estate_reaction_snapshot_issues', '1:N'),
      e('policy_events', 'policy_event_targets', '1:N'),
      e('policy_event_targets', 'real_estate_targets', 'N:1'),
    ],
  },
];

const html = `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>너나사 부동산 ERD - SSAFY 관통프로젝트 제출용</title>
  <style>
    :root {
      --ink: #16202d;
      --muted: #596779;
      --line: #d4dde9;
      --soft: #f6f8fb;
      --paper: #ffffff;
      font-family: "Malgun Gothic", "Apple SD Gothic Neo", "Noto Sans KR", Arial, sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: #e9eef5; color: var(--ink); line-height: 1.48; }
    code { font-family: "Cascadia Mono", Consolas, monospace; }
    .book { width: min(1280px, calc(100vw - 32px)); margin: 20px auto; background: var(--paper); box-shadow: 0 14px 40px rgba(15, 23, 42, 0.14); }
    .sheet { padding: 28px 42px; min-height: 890px; break-after: page; border-bottom: 1px solid var(--line); }
    .sheet.compact { min-height: auto; }
    .kicker { color: var(--muted); font-weight: 800; font-size: 13px; }
    h1 { margin: 8px 0 12px; font-size: 36px; letter-spacing: 0; line-height: 1.14; }
    h2 { margin: 0 0 10px; font-size: 26px; letter-spacing: 0; }
    h3 { margin: 0 0 8px; font-size: 18px; }
    p { margin: 0 0 16px; color: #3d4b5f; }
    .hero-grid { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 22px; align-items: start; margin-top: 18px; }
    .principles { display: grid; gap: 10px; }
    .principle { border: 1px solid var(--line); background: #f8fafc; padding: 14px 16px; }
    .principle strong { display: block; margin-bottom: 5px; }
    .stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 10px 0 10px; }
    .stat { border: 1px solid var(--line); padding: 10px 12px; background: #fff; min-height: 62px; }
    .stat span { display: block; color: var(--muted); font-size: 12px; font-weight: 800; }
    .stat strong { display: block; margin-top: 3px; font-size: 22px; }
    .legend { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0 0; }
    .legend span { border: 1px solid var(--line); background: #fff; padding: 7px 9px; font-size: 12px; }
    .diagram-wrap { border: 1px solid var(--line); background: #fbfcfe; padding: 10px; }
    .overview-diagram { margin-top: 8px; }
    svg.diagram { width: 100%; height: auto; display: block; }
    .hero-title { margin-bottom: 8px; }
    .hero-title h1 { font-size: 30px; margin-bottom: 6px; }
    .hero-title p { margin-bottom: 8px; }
    .group-label { font-size: 17px; font-weight: 900; fill: #334155; }
    .node-title { font-size: 20px; font-weight: 900; fill: #0f172a; }
    .node-subtitle { font-size: 15px; font-weight: 800; fill: #64748b; }
    .node-field { font-size: 13px; fill: #334155; font-family: "Cascadia Mono", Consolas, monospace; }
    .edge { stroke: #526274; stroke-width: 2.6; fill: none; }
    .edge.logical { stroke-dasharray: 8 7; }
    .edge.physical { stroke: #0f766e; stroke-width: 3.2; }
    .edge-label { font-size: 15px; font-weight: 900; fill: #0f766e; paint-order: stroke; stroke: white; stroke-width: 5px; stroke-linejoin: round; }
    .relation-table, .summary-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .relation-table th, .relation-table td, .summary-table th, .summary-table td { border: 1px solid var(--line); padding: 8px 9px; vertical-align: top; }
    .relation-table th, .summary-table th { background: #f8fafc; text-align: left; }
    .cardinality { color: #0f766e; font-weight: 900; text-align: center; white-space: nowrap; }
    .group-section { margin-top: 18px; break-inside: avoid; }
    .group-section h3 { padding: 10px 12px; border: 1px solid var(--line); margin-bottom: 0; }
    .group-section table { margin-top: -1px; }
    .row-count { color: #64748b; white-space: nowrap; text-align: right; }
    footer { color: #64748b; font-size: 12px; padding-top: 12px; border-top: 1px solid var(--line); margin-top: 18px; }
    @page { size: A4 landscape; margin: 10mm; }
    @media print {
      body { background: white; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      .book { width: auto; margin: 0; box-shadow: none; }
      .sheet { border-bottom: 0; padding: 0; min-height: auto; }
      .sheet:not(:last-child) { break-after: page; }
      .diagram-wrap { padding: 8px; }
      .hero-title h1 { font-size: 24px; margin: 4px 0; }
      .hero-title p { font-size: 13px; margin-bottom: 5px; }
      .stats { display: flex; gap: 6px; margin: 5px 0; }
      .stat { min-height: 0; padding: 5px 8px; }
      .stat span { display: inline; font-size: 10px; margin-right: 5px; }
      .stat strong { display: inline; font-size: 14px; }
      .legend { margin: 5px 0; }
      .legend span { padding: 4px 6px; font-size: 10px; }
      .overview-diagram svg.diagram { width: auto; height: 510px; margin: 0 auto; }
      .sheet:first-of-type .stats, .sheet:first-of-type .legend, footer { display: none; }
      .summary-table, .relation-table { font-size: 12px; }
    }
  </style>
</head>
<body>
  <main class="book">
    <section class="sheet">
      <div class="hero-title">
        <div class="kicker">SSAFY 관통프로젝트 제출용 ERD | MySQL/Flyway V${escapeHtml(latestFlyway.version)} | 2026-06-25</div>
        <h1>너나사 부동산 데이터베이스 ERD</h1>
        <p>테이블 목록보다 관계를 먼저 보여주는 제출용 ERD입니다. 중심 엔티티는 <strong>real_estate_targets</strong>이고, 모든 주요 기능은 target_id로 연결됩니다.</p>
      </div>
      <h2>${escapeHtml(diagrams[0].title)}</h2>
      <p>${escapeHtml(diagrams[0].lead)}</p>
      <div class="diagram-wrap overview-diagram">${renderSvg(diagrams[0])}</div>
      <div class="stats">
        <div class="stat"><span>관계도 포함 테이블</span><strong>${Object.keys(tables).length}</strong></div>
        <div class="stat"><span>주요 관계</span><strong>${relationRows.length}</strong></div>
        <div class="stat"><span>중심 엔티티</span><strong>target</strong></div>
        <div class="stat"><span>검증 DB row</span><strong>${formatNumber(sumRows(Object.keys(tables)))}</strong></div>
      </div>
      <div class="legend"><span>실선: 물리 FK</span><span>점선: 논리 FK/애플리케이션 참조</span><span>1:N, 1:0..1, N:M: 관계 수</span></div>
    </section>
    ${diagrams.slice(1).map(renderDiagramSection).join('\n')}
    <section class="sheet compact">
      <h2>주요 관계 목록</h2>
      <p>다이어그램의 선을 표로 다시 정리한 것입니다. 물리 FK가 없는 곳도 서비스 contract상 같은 식별자로 연결되는 경우에는 논리 관계로 표시했습니다.</p>
      ${renderRelationTable()}
    </section>
    <section class="sheet compact">
      <h2>엔티티 요약</h2>
      <p>부록은 컬럼 전체 나열이 아니라 ERD를 읽는 데 필요한 PK/FK와 역할 중심으로 줄였습니다.</p>
      ${groups.map(renderGroupSummary).join('\n')}
      <footer>기준: Docker MySQL <code>youbuyfirst</code>, Flyway latest <code>${escapeHtml(latestFlyway.script)}</code>. Row 수는 현재 로컬 검증 DB의 InnoDB 추정치라 구조 설명 보조값입니다.</footer>
    </section>
  </main>
</body>
</html>`;

mkdirSync(dirname(outPdfHtml), { recursive: true });
writeFileSync(outHtml, html, 'utf8');
writeFileSync(outPdfHtml, html, 'utf8');
console.log(outHtml);
console.log(outPdfHtml);

function n(id, x, y, w, h, tone, fields = null) {
  return { id, x, y, w, h, tone, fields: fields ?? tables[id]?.slice(1) ?? [] };
}

function e(from, to, label, kind = 'logical') {
  return { from, to, label, kind };
}

function renderDiagramSection(diagram) {
  return `<section class="sheet">
    <h2>${escapeHtml(diagram.title)}</h2>
    <p>${escapeHtml(diagram.lead)}</p>
    <div class="diagram-wrap">${renderSvg(diagram)}</div>
  </section>`;
}

function renderSvg(diagram) {
  const nodes = new Map(diagram.nodes.map((node) => [node.id, node]));
  const groupsMarkup = (diagram.groups ?? [])
    .map(([label, x, y, w, h, color]) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="18" fill="${color}" stroke="#d3dce8"/><text x="${x + 18}" y="${y + 34}" class="group-label">${escapeHtml(label)}</text>`)
    .join('\n');
  const edgesMarkup = diagram.edges.map((edge) => renderEdge(edge, nodes)).join('\n');
  const nodesMarkup = diagram.nodes.map(renderNode).join('\n');
  return `<svg class="diagram" viewBox="0 0 ${diagram.width} ${diagram.height}" role="img" aria-label="${escapeHtml(diagram.title)}">
    <defs>
      <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L8,3 z" fill="#526274"></path>
      </marker>
      <marker id="arrowPhysical" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L8,3 z" fill="#0f766e"></path>
      </marker>
    </defs>
    ${groupsMarkup}
    ${edgesMarkup}
    ${nodesMarkup}
  </svg>`;
}

function renderNode(node) {
  const [ko] = tables[node.id] ?? [node.id];
  const fill = {
    user: '#fff8fa',
    target: '#fffaf1',
    ingest: '#f3f8ff',
    market: '#f5fff8',
    report: '#faf8ff',
    comm: '#f8fafc',
  }[node.tone] ?? '#ffffff';
  const stroke = {
    user: '#ef9fb0',
    target: '#efa83f',
    ingest: '#9cc6f6',
    market: '#94d3ad',
    report: '#b6a4ee',
    comm: '#bac4d1',
  }[node.tone] ?? '#cbd5e1';
  const titleLines = wrapTableName(node.id);
  const titleFont = titleLines.length > 1 ? 16 : 19;
  const titleText = titleLines
    .map((line, index) => `<text x="${node.x + 14}" y="${node.y + 25 + index * 17}" class="node-title" style="font-size:${titleFont}px">${escapeHtml(line)}</text>`)
    .join('\n');
  const subtitleY = node.y + 43 + (titleLines.length - 1) * 17;
  const rows = node.h <= 72 ? [] : node.fields.slice(0, 4);
  const fieldText = rows
    .map((field, index) => `<text x="${node.x + 14}" y="${subtitleY + 18 + index * 17}" class="node-field">${escapeHtml(field)}</text>`)
    .join('\n');
  return `<g>
    <rect x="${node.x}" y="${node.y}" width="${node.w}" height="${node.h}" rx="10" fill="${fill}" stroke="${stroke}" stroke-width="2.4"/>
    ${titleText}
    <text x="${node.x + 14}" y="${subtitleY}" class="node-subtitle">${escapeHtml(ko)}</text>
    ${fieldText}
  </g>`;
}

function wrapTableName(name) {
  const parts = name.split('_');
  const lines = [];
  let line = '';
  for (const part of parts) {
    const candidate = line ? `${line}_${part}` : part;
    if (candidate.length <= 22 || !line) {
      line = candidate;
    } else {
      lines.push(line);
      line = part;
    }
  }
  if (line) lines.push(line);
  return lines.slice(0, 3);
}

function renderEdge(edge, nodes) {
  const from = nodes.get(edge.from);
  const to = nodes.get(edge.to);
  if (!from || !to) return '';
  if (edge.from === edge.to) {
    const x = from.x - 30;
    const y = from.y + from.h / 2;
    return `<path d="M ${from.x} ${y} C ${x} ${y - 80}, ${x} ${y + 80}, ${from.x} ${y + 12}" class="edge ${edge.kind}" marker-end="url(#arrow)"/><text x="${x - 18}" y="${y - 4}" class="edge-label">${escapeHtml(edge.label)}</text>`;
  }
  const p1 = anchor(from, to);
  const p2 = anchor(to, from);
  const midX = (p1.x + p2.x) / 2;
  const midY = (p1.y + p2.y) / 2;
  const marker = edge.kind === 'physical' ? 'arrowPhysical' : 'arrow';
  return `<line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" class="edge ${edge.kind}" marker-end="url(#${marker})"/><text x="${midX}" y="${midY - 8}" text-anchor="middle" class="edge-label">${escapeHtml(edge.label)}</text>`;
}

function anchor(node, other) {
  const cx = node.x + node.w / 2;
  const cy = node.y + node.h / 2;
  const ocx = other.x + other.w / 2;
  const ocy = other.y + other.h / 2;
  const dx = ocx - cx;
  const dy = ocy - cy;
  if (Math.abs(dx) > Math.abs(dy)) {
    return { x: dx > 0 ? node.x + node.w : node.x, y: cy };
  }
  return { x: cx, y: dy > 0 ? node.y + node.h : node.y };
}

function renderRelationTable() {
  const rows = relationRows.map(([from, card, to, key, meaning]) => `<tr>
    <td><code>${escapeHtml(from)}</code></td>
    <td class="cardinality">${escapeHtml(card)}</td>
    <td><code>${escapeHtml(to)}</code></td>
    <td><code>${escapeHtml(key)}</code></td>
    <td>${escapeHtml(meaning)}</td>
  </tr>`).join('\n');
  return `<table class="relation-table"><thead><tr><th>부모/기준</th><th>관계</th><th>자식/참조</th><th>연결 키</th><th>의미</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderGroupSummary(group) {
  const rows = group.tables.map((table) => {
    const [ko, key, refs] = tables[table];
    return `<tr>
      <td><code>${escapeHtml(table)}</code><br><span>${escapeHtml(ko)}</span></td>
      <td>${escapeHtml(key)}</td>
      <td>${escapeHtml(refs)}</td>
      <td class="row-count">${formatNumber(tableRows.get(table) ?? 0)}</td>
    </tr>`;
  }).join('\n');
  return `<div class="group-section"><h3 style="background:${group.color}">${escapeHtml(group.title)}</h3><table class="summary-table"><thead><tr><th>엔티티</th><th>PK</th><th>주요 연결 키</th><th>현재 row</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function loadTableRows() {
  try {
    const out = execFileSync('docker', [
      'exec',
      'youbuyfirst_realestate-mysql-1',
      'mysql',
      '-uyoubuyfirst',
      '-pyoubuyfirst',
      '-D',
      'youbuyfirst',
      '--batch',
      '--raw',
      '--skip-column-names',
      '-e',
      "SELECT table_name, COALESCE(table_rows, 0) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE' ORDER BY table_name",
    ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    return new Map(out.trim().split(/\r?\n/).filter(Boolean).map((line) => {
      const [table, rows] = line.split('\t');
      return [table, Number(rows || 0)];
    }));
  } catch {
    return new Map();
  }
}

function loadLatestFlyway() {
  try {
    const out = execFileSync('docker', [
      'exec',
      'youbuyfirst_realestate-mysql-1',
      'mysql',
      '-uyoubuyfirst',
      '-pyoubuyfirst',
      '-D',
      'youbuyfirst',
      '--batch',
      '--raw',
      '--skip-column-names',
      '-e',
      "SELECT version, script FROM flyway_schema_history WHERE success = 1 AND version IS NOT NULL ORDER BY installed_rank DESC LIMIT 1",
    ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    const [version = '-', script = '-'] = out.trim().split('\t');
    return { version, script };
  } catch {
    return { version: '-', script: '-' };
  }
}

function sumRows(tableNames) {
  return tableNames.reduce((sum, table) => sum + (tableRows.get(table) ?? 0), 0);
}

function formatNumber(value) {
  return Number(value).toLocaleString('ko-KR');
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
