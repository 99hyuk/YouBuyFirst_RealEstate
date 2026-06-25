package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.realestate.batch.RealEstateExternalFetchClient;
import com.youbuyfirst.backend.realestate.batch.RealEstateExternalFetchResult;
import com.youbuyfirst.backend.realestate.dto.MarketDataScheduleEventResponse;
import com.youbuyfirst.backend.realestate.dto.MarketDataScheduleResponse;
import com.youbuyfirst.backend.realestate.dto.MarketDataSourceLinkResponse;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.util.HtmlUtils;

import java.net.URI;
import java.time.Instant;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
public class MarketDataScheduleService {

    private static final ZoneId SEOUL_ZONE = ZoneId.of("Asia/Seoul");
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
    private static final String REB_BULLETIN_SEARCH_URL = "https://www.reb.or.kr/r-one/portal/bbs/pres/searchBulletin.do";
    private static final String REB_BULLETIN_DETAIL_URL = "https://www.reb.or.kr/r-one/portal/bbs/pres/selectBulletinPage.do";
    private static final String REB_STAT_SCHEDULE_URL = "https://www.reb.or.kr/r-one/portal/compose/scheduleStatsPage.do";
    private static final String REB_STAT_DETAIL_URL = "https://www.reb.or.kr/r-one/portal/stat/easyStatPage.do";
    private static final String MOLIT_POLICY_LIST_URL = "https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp";
    private static final String MOLIT_STAT_SCHEDULE_URL = "https://stat.molit.go.kr/portal/notice/scheduleList.do";
    private static final String APPLYHOME_APT_LIST_URL = "https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancListView.do";
    private static final String APPLYHOME_APT_DETAIL_URL = "https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancDetail.do";
    private static final String BOK_RATE_SCHEDULE_URL = "https://www.bok.or.kr/portal/singl/crncyPolicyDrcMtg/listYear.do?menuNo=200755&mtgSe=A";
    private static final String BOK_STAT_SCHEDULE_URL = "https://www.bok.or.kr/portal/stats/statsPublictSchdul/listCldr.do?menuNo=200775";
    private static final String HUG_PRIVATE_APT_STAT_URL = "https://khug.or.kr/houstar/web/p01/03/p010301.jsp?currentPage=1";
    private static final String LH_PUBLIC_SALE_LIST_URL = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1027";
    private static final String LH_PUBLIC_RENT_LIST_URL = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1026";
    private static final String LH_PUBLIC_DETAIL_URL = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do";
    private static final String SH_PUBLIC_LEASE_LIST_URL = "https://housing.seoul.go.kr/site/main/sh/publicLease/07/list";
    private static final String GH_PUBLIC_SUPPLY_LIST_URL = "https://www.gh.or.kr/gh/announcement-of-salerental001.do";
    private static final String IH_RENT_NOTICE_LIST_URL = "https://www.ih.co.kr/main/sale_lease/notice.jsp";
    private static final String IH_HOUSE_NOTICE_LIST_URL = "https://www.ih.co.kr/main/sale_lease/board/house_notice.jsp";
    private static final String FSC_PRESS_LIST_URL = "https://www.fsc.go.kr/no010101";
    private static final String REALTY_PRICE_BOARD_URL = "https://www.realtyprice.kr/notice/board/boardListAll.board";
    private static final String REALTY_PRICE_DETAIL_URL = "https://www.realtyprice.kr/notice/board/boardDetailAll.board";
    private static final Pattern TABLE_ROW_PATTERN = Pattern.compile("(?is)<tr\\b([^>]*)>(.*?)</tr>");
    private static final Pattern LIST_ITEM_PATTERN = Pattern.compile("(?is)<li\\b[^>]*>(.*?)</li>");
    private static final Pattern TABLE_CELL_PATTERN = Pattern.compile("(?is)<t[dh]\\b[^>]*>(.*?)</t[dh]>");
    private static final Pattern TABLE_CELL_WITH_ID_PATTERN = Pattern.compile("(?is)<td\\b([^>]*)\\bid=\"(\\d{8})\"[^>]*>(.*?)</td>");
    private static final Pattern MOLIT_TITLE_LINK_PATTERN = Pattern.compile("(?is)<td\\b[^>]*class=\"[^\"]*\\bbd_title\\b[^\"]*\"[^>]*>.*?<a\\b[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>");
    private static final Pattern REB_SCHEDULE_LINK_PATTERN = Pattern.compile("(?is)<p\\b[^>]*\\bdata-relId=\"([^\"]+)\"[^>]*>.*?<a\\b[^>]*>(.*?)</a>.*?</p>");
    private static final Pattern LINK_PATTERN = Pattern.compile("(?is)<a\\b[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>");
    private static final Pattern REALTY_PRICE_DETAIL_PATTERN = Pattern.compile("(?is)goDetail\\(\\s*(\\d+)\\s*\\)");
    private static final Pattern ISO_DATE_PATTERN = Pattern.compile("\\d{4}-\\d{2}-\\d{2}");
    private static final Pattern DOT_DATE_PATTERN = Pattern.compile("(?<!\\d)(\\d{4})[./](\\d{1,2})[./](\\d{1,2})(?!\\d)");
    private static final Pattern SHORT_DOT_DATE_PATTERN = Pattern.compile("(?<!\\d)(\\d{2})\\.(\\d{1,2})\\.(\\d{1,2})(?!\\d)");
    private static final Pattern KOREAN_MONTH_DAY_PATTERN = Pattern.compile("(\\d{1,2})\\s*월\\s*(\\d{1,2})\\s*일");
    private static final Set<String> MOLIT_RELEVANT_FIELDS = Set.of("주택토지");
    private static final List<String> MOLIT_RELEVANT_TITLE_TERMS = List.of(
            "부동산",
            "주택",
            "전세",
            "월세",
            "임대",
            "공급",
            "분양",
            "청약",
            "대출",
            "정비",
            "재개발",
            "재건축",
            "택지",
            "공공주택",
            "안심전세"
    );
    private static final List<String> MOLIT_STAT_RELEVANT_TITLE_TERMS = List.of(
            "미분양",
            "주택건설",
            "주택공급",
            "건축허가",
            "착공",
            "준공",
            "공동주택",
            "지가변동",
            "부동산거래",
            "전월세"
    );
    private static final List<String> HUG_RELEVANT_TITLE_TERMS = List.of(
            "민간아파트",
            "분양가격",
            "분양가",
            "초기분양률",
            "분양시장",
            "대지비",
            "주택보증통계"
    );
    private static final List<String> PUBLIC_SUPPLY_RELEVANT_TITLE_TERMS = List.of(
            "입주자모집",
            "입주자 모집",
            "공공주택",
            "공공분양",
            "분양 공고",
            "분양주택",
            "행복주택",
            "국민임대",
            "영구임대",
            "장기전세",
            "전세임대",
            "매입임대",
            "공공임대",
            "주택 공급",
            "주택분양",
            "예비입주자"
    );
    private static final List<String> LH_MAJOR_SUPPLY_TITLE_TERMS = List.of(
            "공공분양",
            "공공분양주택",
            "분양주택",
            "공공임대주택리츠",
            "공공임대리츠",
            "토지임대부"
    );
    private static final List<String> LH_LOW_SIGNAL_TITLE_TERMS = List.of(
            "정정공고",
            "예비입주자",
            "예비 입주자",
            "행복주택",
            "국민임대",
            "영구임대",
            "매입임대",
            "전세임대",
            "고령자",
            "청년",
            "기숙사형",
            "자격완화",
            "일반매각",
            "선착순",
            "잔여주택",
            "동호지정"
    );
    private static final List<String> FINANCE_POLICY_RELEVANT_TITLE_TERMS = List.of(
            "부동산",
            "주담대",
            "주택담보",
            "가계부채",
            "가계대출",
            "전세대출",
            "프로젝트금융",
            " PF",
            "LTV",
            "DSR",
            "대출규제"
    );
    private static final List<String> BOK_STAT_RELEVANT_TITLE_TERMS = List.of(
            "자금순환",
            "통화 및 유동성",
            "국민대차대조표",
            "생산자물가지수",
            "국내총생산",
            "금융기관 가중평균금리",
            "소비자동향조사",
            "기업경기조사",
            "경제심리지수"
    );
    private static final List<String> OFFICIAL_PRICE_RELEVANT_TITLE_TERMS = List.of(
            "공동주택가격",
            "공시가격",
            "결정·공시",
            "열람",
            "의견제출",
            "이의신청"
    );
    private static final List<RebBulletinCategory> REB_BULLETIN_CATEGORIES = List.of(
            new RebBulletinCategory("PRES01", "가격지수", "market"),
            new RebBulletinCategory("PRES02", "가격지수", "market"),
            new RebBulletinCategory("PRES05", "가격지수", "market"),
            new RebBulletinCategory("PRES06", "전세", "deal"),
            new RebBulletinCategory("PRES07", "거래현황", "deal")
    );

    private static final List<SourceDefinition> SOURCES = List.of(
            new SourceDefinition("reb-r-one", "한국부동산원 R-ONE", "가격지수·거래현황 공표일정", "reb", REB_STAT_SCHEDULE_URL, "가격지수", "market"),
            new SourceDefinition("rt-molit", "국토교통부 실거래가 공개시스템", "상시 공개·freshness 확인", "molit", "https://rt.molit.go.kr/", "실거래", "deal"),
            new SourceDefinition("molit-stat", "국토교통 통계누리", "미분양·공급", "molit", "https://stat.molit.go.kr/", "공급", "supply"),
            new SourceDefinition("bok-rate", "한국은행 일정", "금리·통화정책", "bok", BOK_RATE_SCHEDULE_URL, "금융", "finance"),
            new SourceDefinition("bok-stat", "한국은행 경제통계", "금융·거시 통계 공표", "bok", BOK_STAT_SCHEDULE_URL, "금융", "finance"),
            new SourceDefinition("applyhome", "청약Home", "청약·분양", "applyhome", "https://applyhome.co.kr/", "청약", "subscription"),
            new SourceDefinition("molit-policy", "국토교통부", "정책·보도자료", "molit", "https://www.molit.go.kr/", "정책", "policy"),
            new SourceDefinition("hug-market", "HUG 주택도시보증공사", "분양가격·분양시장", "hug", HUG_PRIVATE_APT_STAT_URL, "보증", "supply"),
            new SourceDefinition("lh-apply", "LH청약플러스", "공공분양·공공임대", "lh", LH_PUBLIC_SALE_LIST_URL, "공급", "supply"),
            new SourceDefinition("sh-housing", "서울주거포털 SH", "공공임대", "sh", SH_PUBLIC_LEASE_LIST_URL, "공급", "supply"),
            new SourceDefinition("gh-supply", "경기주택도시공사 GH", "분양·임대 공고", "gh", GH_PUBLIC_SUPPLY_LIST_URL, "공급", "supply"),
            new SourceDefinition("ih-supply", "인천도시공사 iH", "분양·임대 공고", "ih", IH_RENT_NOTICE_LIST_URL, "공급", "supply"),
            new SourceDefinition("fsc-policy", "금융위원회", "부동산 금융정책", "fsc", FSC_PRESS_LIST_URL, "금융", "finance"),
            new SourceDefinition("realty-price", "부동산공시가격 알리미", "공시가격", "reb", REALTY_PRICE_BOARD_URL, "공시가격", "market")
    );

    private final MarketDataSourceRepository sourceRepository;
    private final MarketDataScheduleRepository scheduleRepository;
    private final RealEstateExternalFetchClient fetchClient;

    public MarketDataScheduleService(
            MarketDataSourceRepository sourceRepository,
            MarketDataScheduleRepository scheduleRepository,
            RealEstateExternalFetchClient fetchClient
    ) {
        this.sourceRepository = sourceRepository;
        this.scheduleRepository = scheduleRepository;
        this.fetchClient = fetchClient;
    }

    @Transactional
    public int refreshMonth(YearMonth month) {
        Instant now = Instant.now();
        Map<String, SourceCheck> sourceChecks = SOURCES.stream()
                .collect(Collectors.toMap(SourceDefinition::id, source -> checkSource(source, now)));
        for (SourceDefinition source : SOURCES) {
            SourceCheck check = sourceChecks.get(source.id());
            MarketDataSource entity = sourceRepository.findById(source.id())
                    .orElseGet(() -> new MarketDataSource(source.id(), now));
            entity.update(
                    source.title(),
                    source.label(),
                    source.provider(),
                    source.url(),
                    source.category(),
                    source.tone(),
                    true,
                    check.checkedAt(),
                    check.stale(),
                    check.status(),
                    now
            );
            sourceRepository.save(entity);
        }

        Map<String, SourceDefinition> sourceById = SOURCES.stream()
                .collect(Collectors.toMap(SourceDefinition::id, Function.identity()));
        List<ScheduleSeed> seeds = scheduleSeeds(month).stream()
                .filter(MarketDataScheduleService::hasScheduleContextUrl)
                .toList();
        Set<String> acceptedIds = seeds.stream()
                .map(ScheduleSeed::id)
                .collect(Collectors.toCollection(LinkedHashSet::new));
        int acceptedSchedules = 0;
        for (ScheduleSeed seed : seeds) {
            SourceDefinition source = sourceById.get(seed.sourceId());
            SourceCheck check = sourceChecks.get(seed.sourceId());
            MarketDataSchedule schedule = scheduleRepository.findById(seed.id())
                    .orElseGet(() -> new MarketDataSchedule(seed.id(), now));
            schedule.update(
                    source.id(),
                    seed.date(),
                    seed.title(),
                    seed.category(),
                    source.title(),
                    seed.summary(),
                    seed.linkUrl(),
                    seed.tone(),
                    source.provider(),
                    scheduleStatus(seed, check),
                    scheduleDataStatus(seed, check),
                    scheduleStale(seed, check),
                    check.checkedAt(),
                    seed.date(),
                    now
            );
            scheduleRepository.save(schedule);
            acceptedSchedules++;
        }
        LocalDate start = month.atDay(1);
        LocalDate end = month.atEndOfMonth();
        if (acceptedIds.isEmpty()) {
            scheduleRepository.deleteByScheduleDateBetween(start, end);
        } else {
            scheduleRepository.deleteByScheduleDateBetweenAndIdNotIn(start, end, acceptedIds);
        }
        return acceptedSchedules;
    }

    @Transactional(readOnly = true)
    public MarketDataScheduleResponse listMonth(YearMonth month) {
        LocalDate start = month.atDay(1);
        LocalDate end = month.atEndOfMonth();
        List<MarketDataScheduleEventResponse> events = scheduleRepository
                .findByScheduleDateBetweenOrderByScheduleDateAscTitleAsc(start, end)
                .stream()
                .map(this::toEventResponse)
                .toList();
        List<MarketDataSourceLinkResponse> sources = sourceRepository.findByEnabledTrueOrderByTitleAsc()
                .stream()
                .sorted(Comparator.comparing(source -> source.getTitle()))
                .map(this::toSourceResponse)
                .toList();
        return new MarketDataScheduleResponse(month.toString(), events, sources);
    }

    public YearMonth currentMonth() {
        return YearMonth.now(SEOUL_ZONE);
    }

    private SourceCheck checkSource(SourceDefinition source, Instant now) {
        RealEstateExternalFetchResult result = fetchSafely(source.url());
        boolean ok = result.success();
        return new SourceCheck(
                ok ? "확인 완료" : "확인 필요",
                ok ? "ok" : "error",
                !ok,
                now
        );
    }

    private List<ScheduleSeed> scheduleSeeds(YearMonth month) {
        List<ScheduleSeed> seeds = new ArrayList<>();
        seeds.addAll(collectPublishedScheduleSeeds(month));
        seeds.addAll(collectOfficialScheduleSeeds(month));
        return seeds;
    }

    private List<ScheduleSeed> collectPublishedScheduleSeeds(YearMonth month) {
        List<ScheduleSeed> seeds = new ArrayList<>();
        seeds.addAll(collectRebPublishedSeeds(month));
        seeds.addAll(collectMolitPolicySeeds(month));
        seeds.addAll(collectApplyHomeSeeds(month));
        seeds.addAll(collectHugPublishedSeeds(month));
        seeds.addAll(collectLhPublicSupplySeeds(month));
        seeds.addAll(collectOfficialBoardPublishedSeeds(
                month,
                "sh-housing",
                SH_PUBLIC_LEASE_LIST_URL,
                "서울주거포털 SH",
                "공급",
                "supply",
                PUBLIC_SUPPLY_RELEVANT_TITLE_TERMS
        ));
        seeds.addAll(collectOfficialBoardPublishedSeeds(
                month,
                "gh-supply",
                GH_PUBLIC_SUPPLY_LIST_URL,
                "경기주택도시공사 GH",
                "공급",
                "supply",
                PUBLIC_SUPPLY_RELEVANT_TITLE_TERMS
        ));
        seeds.addAll(collectIhPublicSupplySeeds(month));
        seeds.addAll(collectFscPolicySeeds(month));
        seeds.addAll(collectRealtyPriceNoticeSeeds(month));
        return seeds;
    }

    private List<ScheduleSeed> collectOfficialScheduleSeeds(YearMonth month) {
        List<ScheduleSeed> seeds = new ArrayList<>();
        seeds.addAll(collectRebOfficialScheduleSeeds(month));
        seeds.addAll(collectMolitStatScheduleSeeds(month));
        seeds.addAll(collectBokRateScheduleSeeds(month));
        seeds.addAll(collectBokStatScheduleSeeds(month));
        return seeds;
    }

    private List<ScheduleSeed> collectRebPublishedSeeds(YearMonth month) {
        List<ScheduleSeed> seeds = new ArrayList<>();
        for (RebBulletinCategory category : REB_BULLETIN_CATEGORIES) {
            RealEstateExternalFetchResult result = postFormSafely(
                    REB_BULLETIN_SEARCH_URL,
                    Map.of(
                            "page", "1",
                            "rows", "20",
                            "bbsCd", "PRES",
                            "grpCd", "B1005",
                            "searchType", "",
                            "searchWord", "",
                            "listSubCd", category.code()
                    ),
                    Map.of(
                            "Referer", "https://www.reb.or.kr/r-one/portal/bbs/pres/searchBulletinPage.do?listSubCd=" + category.code(),
                            "X-Requested-With", "XMLHttpRequest"
                    )
            );
            JsonNode root = readJson(result);
            if (root == null || !root.path("data").isArray()) {
                continue;
            }
            for (JsonNode row : root.path("data")) {
                LocalDate publishedDate = parseDate(row.path("userDttm").asText(""));
                if (publishedDate == null || !YearMonth.from(publishedDate).equals(month)) {
                    continue;
                }
                String seq = row.path("seq").asText("");
                String title = row.path("bbsTit").asText("");
                if (isBlank(seq) || isBlank(title)) {
                    continue;
                }
                String listSubName = row.path("listSubNm").asText(category.code());
                String noticeYn = row.path("noticeYn").asText("N");
                String detailUrl = REB_BULLETIN_DETAIL_URL + "?bbsCd=PRES&seq=" + seq + "&noticeYn=" + noticeYn;
                seeds.add(new ScheduleSeed(
                        "reb-r-one-published-" + category.code().toLowerCase() + "-" + seq,
                        "reb-r-one",
                        publishedDate,
                        title,
                        category.category(),
                        "한국부동산원 " + listSubName + " 공표자료: " + title,
                        category.tone(),
                        detailUrl,
                        ScheduleSeedKind.PUBLISHED
                ));
            }
        }
        return seeds;
    }

    private List<ScheduleSeed> collectRebOfficialScheduleSeeds(YearMonth month) {
        RealEstateExternalFetchResult result = fetchSafely(REB_STAT_SCHEDULE_URL);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        List<ScheduleSeed> seeds = new ArrayList<>();
        Matcher cellMatcher = TABLE_CELL_WITH_ID_PATTERN.matcher(result.body());
        while (cellMatcher.find()) {
            LocalDate scheduleDate = parseCompactDate(cellMatcher.group(2));
            if (scheduleDate == null || !YearMonth.from(scheduleDate).equals(month)) {
                continue;
            }

            String cell = cellMatcher.group(3);
            Matcher linkMatcher = REB_SCHEDULE_LINK_PATTERN.matcher(cell);
            while (linkMatcher.find()) {
                String relStatId = cleanHtml(linkMatcher.group(1));
                String title = cleanHtml(linkMatcher.group(2)).replace("새창 열림", "").trim();
                if (isBlank(relStatId) || isBlank(title) || !isRelevantRebOfficialSchedule(title)) {
                    continue;
                }
                seeds.add(new ScheduleSeed(
                        "reb-r-one-schedule-" + relStatId + "-" + scheduleDate,
                        "reb-r-one",
                        scheduleDate,
                        title + " 공표 예정",
                        rebScheduleCategory(title),
                        "R-ONE 통계공표일정 " + scheduleDate + " 기준 " + title + " 공식 공표 일정입니다.",
                        rebScheduleTone(title),
                        REB_STAT_DETAIL_URL + "?cateId=" + relStatId,
                        ScheduleSeedKind.OFFICIAL_SCHEDULE
                ));
            }
        }
        return seeds;
    }

    private List<ScheduleSeed> collectMolitPolicySeeds(YearMonth month) {
        RealEstateExternalFetchResult result = fetchSafely(MOLIT_POLICY_LIST_URL);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        List<ScheduleSeed> seeds = new ArrayList<>();
        Matcher rowMatcher = TABLE_ROW_PATTERN.matcher(result.body());
        while (rowMatcher.find()) {
            String row = rowMatcher.group(2);
            Matcher linkMatcher = MOLIT_TITLE_LINK_PATTERN.matcher(row);
            if (!linkMatcher.find()) {
                continue;
            }

            String title = cleanHtml(linkMatcher.group(2));
            String field = cleanHtml(classCell(row, "bd_field"));
            String dateText = cleanHtml(classCell(row, "bd_date"));
            LocalDate publishedDate = parseDate(dateText);
            if (publishedDate == null || !YearMonth.from(publishedDate).equals(month)) {
                continue;
            }
            if (!isRelevantMolitPolicy(field, title)) {
                continue;
            }

            String href = HtmlUtils.htmlUnescape(linkMatcher.group(1));
            String linkUrl = absoluteUrl(MOLIT_POLICY_LIST_URL, href);
            String providerObjectId = queryParam(linkUrl, "id");
            String idSuffix = isBlank(providerObjectId)
                    ? Integer.toUnsignedString((publishedDate + ":" + title + ":" + linkUrl).hashCode(), 36)
                    : providerObjectId;
            seeds.add(new ScheduleSeed(
                    "molit-policy-published-" + idSuffix,
                    "molit-policy",
                    publishedDate,
                    title,
                    "정책",
                    "국토교통부 " + field + " 보도자료: " + title,
                    "policy",
                    linkUrl,
                    ScheduleSeedKind.PUBLISHED
            ));
        }
        return seeds;
    }

    private List<ScheduleSeed> collectMolitStatScheduleSeeds(YearMonth month) {
        RealEstateExternalFetchResult result = fetchSafely(MOLIT_STAT_SCHEDULE_URL);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        List<ScheduleSeed> seeds = new ArrayList<>();
        Matcher rowMatcher = TABLE_ROW_PATTERN.matcher(result.body());
        while (rowMatcher.find()) {
            String row = rowMatcher.group(2);
            Matcher linkMatcher = LINK_PATTERN.matcher(row);
            String href = null;
            String statName = null;
            while (linkMatcher.find()) {
                String candidateHref = HtmlUtils.htmlUnescape(linkMatcher.group(1));
                if (!candidateHref.contains("viewChk.do")) {
                    continue;
                }
                href = candidateHref;
                statName = cleanHtml(linkMatcher.group(2));
                break;
            }
            if (isBlank(href) || isBlank(statName) || !isRelevantMolitStat(statName)) {
                continue;
            }

            LocalDate scheduleDate = firstDateInMonth(dateStrings(row), month);
            if (scheduleDate == null) {
                continue;
            }

            String linkUrl = absoluteUrl(MOLIT_STAT_SCHEDULE_URL, href);
            String statId = queryParam(linkUrl, "hRsId");
            String idSuffix = isBlank(statId)
                    ? Integer.toUnsignedString((scheduleDate + ":" + statName + ":" + linkUrl).hashCode(), 36)
                    : statId;
            seeds.add(new ScheduleSeed(
                    "molit-stat-schedule-" + idSuffix + "-" + scheduleDate,
                    "molit-stat",
                    scheduleDate,
                    statName + " 공표 예정",
                    "공급",
                    "통계누리 다음공표일 " + scheduleDate + " 기준 " + statName + " 공식 통계 일정입니다.",
                    "supply",
                    linkUrl,
                    ScheduleSeedKind.OFFICIAL_SCHEDULE
            ));
        }
        return seeds;
    }

    private List<ScheduleSeed> collectApplyHomeSeeds(YearMonth month) {
        RealEstateExternalFetchResult result = fetchSafely(APPLYHOME_APT_LIST_URL);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        List<ScheduleSeed> seeds = new ArrayList<>();
        Matcher rowMatcher = TABLE_ROW_PATTERN.matcher(result.body());
        while (rowMatcher.find()) {
            String attributes = rowMatcher.group(1);
            String row = rowMatcher.group(2);
            String pblancNo = attribute(attributes, "data-pbno");
            String houseManageNo = attribute(attributes, "data-hmno");
            String houseName = cleanHtml(attribute(attributes, "data-honm"));
            if (isBlank(pblancNo) || isBlank(houseManageNo) || isBlank(houseName)) {
                continue;
            }

            List<String> dates = dateStrings(row);
            if (dates.isEmpty()) {
                continue;
            }
            LocalDate noticeDate = parseDate(dates.get(0));
            String detailUrl = APPLYHOME_APT_DETAIL_URL + "?houseManageNo=" + houseManageNo + "&pblancNo=" + pblancNo;

            if (noticeDate != null && YearMonth.from(noticeDate).equals(month)) {
                seeds.add(new ScheduleSeed(
                        "applyhome-published-" + pblancNo,
                        "applyhome",
                        noticeDate,
                        houseName + " 입주자모집공고",
                        "청약",
                        applyHomeSummary(dates),
                        "subscription",
                        detailUrl,
                        ScheduleSeedKind.PUBLISHED
                ));
            }

            if (dates.size() >= 3) {
                LocalDate applicationStartDate = parseDate(dates.get(1));
                LocalDate applicationEndDate = parseDate(dates.get(2));
                if (applicationStartDate != null && YearMonth.from(applicationStartDate).equals(month)) {
                    seeds.add(new ScheduleSeed(
                            "applyhome-application-start-" + pblancNo + "-" + applicationStartDate,
                            "applyhome",
                            applicationStartDate,
                            houseName + " 청약 접수 시작",
                            "청약",
                            "청약Home 공식 공고 기준 접수기간 " + dates.get(1) + "~" + dates.get(2) + " 일정입니다.",
                            "subscription",
                            detailUrl,
                            ScheduleSeedKind.OFFICIAL_SCHEDULE
                    ));
                }
                if (applicationEndDate != null && !applicationEndDate.equals(applicationStartDate)
                        && YearMonth.from(applicationEndDate).equals(month)) {
                    seeds.add(new ScheduleSeed(
                            "applyhome-application-end-" + pblancNo + "-" + applicationEndDate,
                            "applyhome",
                            applicationEndDate,
                            houseName + " 청약 접수 마감",
                            "청약",
                            "청약Home 공식 공고 기준 접수 마감일 " + dates.get(2) + " 일정입니다.",
                            "subscription",
                            detailUrl,
                            ScheduleSeedKind.OFFICIAL_SCHEDULE
                    ));
                }
            }

            if (dates.size() >= 4) {
                LocalDate winnerDate = parseDate(dates.get(3));
                if (winnerDate != null && YearMonth.from(winnerDate).equals(month)) {
                    seeds.add(new ScheduleSeed(
                            "applyhome-winner-" + pblancNo + "-" + winnerDate,
                            "applyhome",
                            winnerDate,
                            houseName + " 당첨자 발표",
                            "청약",
                            "청약Home 공식 공고 기준 당첨자 발표일 " + dates.get(3) + " 일정입니다.",
                            "subscription",
                            detailUrl,
                            ScheduleSeedKind.OFFICIAL_SCHEDULE
                    ));
                }
            }
        }
        return seeds;
    }

    private List<ScheduleSeed> collectHugPublishedSeeds(YearMonth month) {
        RealEstateExternalFetchResult result = fetchSafely(HUG_PRIVATE_APT_STAT_URL);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        List<ScheduleSeed> seeds = new ArrayList<>();
        Matcher rowMatcher = TABLE_ROW_PATTERN.matcher(result.body());
        while (rowMatcher.find()) {
            String row = rowMatcher.group(2);
            Matcher linkMatcher = LINK_PATTERN.matcher(row);
            String href = null;
            String title = null;
            while (linkMatcher.find()) {
                String candidateHref = HtmlUtils.htmlUnescape(linkMatcher.group(1));
                String candidateTitle = cleanHtml(linkMatcher.group(2));
                if (!candidateHref.contains("articleId=") || !isRelevantHugTitle(candidateTitle)) {
                    continue;
                }
                href = candidateHref;
                title = candidateTitle;
                break;
            }
            if (isBlank(href) || isBlank(title)) {
                continue;
            }

            LocalDate publishedDate = firstDateInMonth(dateStrings(row), month);
            if (publishedDate == null) {
                continue;
            }

            String linkUrl = absoluteUrl(HUG_PRIVATE_APT_STAT_URL, href);
            String articleId = queryParam(linkUrl, "articleId");
            String idSuffix = isBlank(articleId)
                    ? Integer.toUnsignedString((publishedDate + ":" + title + ":" + linkUrl).hashCode(), 36)
                    : articleId;
            seeds.add(new ScheduleSeed(
                    "hug-market-published-" + idSuffix,
                    "hug-market",
                    publishedDate,
                    title,
                    "보증",
                    "HUG 주택도시보증공사 분양시장 공표자료: " + title,
                    "supply",
                    linkUrl,
                    ScheduleSeedKind.PUBLISHED
            ));
        }
        return seeds;
    }

    private List<ScheduleSeed> collectLhPublicSupplySeeds(YearMonth month) {
        List<ScheduleSeed> seeds = new ArrayList<>();
        seeds.addAll(collectLhPublicSupplySeeds(month, LH_PUBLIC_SALE_LIST_URL));
        seeds.addAll(collectLhPublicSupplySeeds(month, LH_PUBLIC_RENT_LIST_URL));
        return seeds;
    }

    private List<ScheduleSeed> collectLhPublicSupplySeeds(YearMonth month, String sourceUrl) {
        RealEstateExternalFetchResult result = fetchSafely(sourceUrl);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        List<ScheduleSeed> seeds = new ArrayList<>();
        for (String block : htmlBlocks(result.body())) {
            String title = firstRelevantText(block, PUBLIC_SUPPLY_RELEVANT_TITLE_TERMS);
            if (isBlank(title) || !isRelevantLhPublicSupplyTitle(title)) {
                continue;
            }
            LocalDate publishedDate = firstDateInMonth(dateStrings(block), month);
            if (publishedDate == null) {
                continue;
            }

            String panId = attribute(block, "data-id1");
            String detailUrl = lhPublicSupplyDetailUrl(block);
            if (isBlank(panId) || isBlank(detailUrl)) {
                continue;
            }
            seeds.add(new ScheduleSeed(
                    "lh-apply-published-" + panId + "-" + publishedDate,
                    "lh-apply",
                    publishedDate,
                    title,
                    "공급",
                    "LH청약플러스 공식 공급 공고: " + title,
                    "supply",
                    detailUrl,
                    ScheduleSeedKind.PUBLISHED
            ));
        }
        return seeds;
    }

    private List<ScheduleSeed> collectIhPublicSupplySeeds(YearMonth month) {
        List<ScheduleSeed> seeds = new ArrayList<>();
        seeds.addAll(collectOfficialBoardPublishedSeeds(
                month,
                "ih-supply",
                IH_RENT_NOTICE_LIST_URL,
                "인천도시공사 iH",
                "공급",
                "supply",
                PUBLIC_SUPPLY_RELEVANT_TITLE_TERMS
        ));
        seeds.addAll(collectOfficialBoardPublishedSeeds(
                month,
                "ih-supply",
                IH_HOUSE_NOTICE_LIST_URL,
                "인천도시공사 iH",
                "공급",
                "supply",
                PUBLIC_SUPPLY_RELEVANT_TITLE_TERMS
        ));
        return seeds;
    }

    private List<ScheduleSeed> collectOfficialBoardPublishedSeeds(
            YearMonth month,
            String sourceId,
            String sourceUrl,
            String sourceTitle,
            String category,
            String tone,
            List<String> relevantTerms
    ) {
        RealEstateExternalFetchResult result = fetchSafely(sourceUrl);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        List<ScheduleSeed> seeds = new ArrayList<>();
        for (String block : htmlBlocks(result.body())) {
            Matcher linkMatcher = LINK_PATTERN.matcher(block);
            while (linkMatcher.find()) {
                String href = HtmlUtils.htmlUnescape(linkMatcher.group(1)).trim();
                String title = cleanHtml(linkMatcher.group(2));
                if (isPlaceholderHref(href) || isBlank(title) || !relevantTerms.stream().anyMatch(title::contains)) {
                    continue;
                }
                if (PUBLIC_SUPPLY_RELEVANT_TITLE_TERMS.equals(relevantTerms) && !isRelevantPublicSupplyTitle(title)) {
                    continue;
                }

                LocalDate publishedDate = firstDateInMonth(dateStrings(block), month);
                if (publishedDate == null) {
                    continue;
                }

                String linkUrl = absoluteUrl(sourceUrl, href);
                if (isListOnlyUrl(sourceUrl, linkUrl)) {
                    continue;
                }
                String idSuffix = boardIdSuffix(linkUrl, publishedDate, title);
                seeds.add(new ScheduleSeed(
                        sourceId + "-published-" + idSuffix + "-" + publishedDate,
                        sourceId,
                        publishedDate,
                        title,
                        category,
                        sourceTitle + " 공식 공급 공고: " + title,
                        tone,
                        linkUrl,
                        ScheduleSeedKind.PUBLISHED
                ));
                break;
            }
        }
        return seeds;
    }

    private List<ScheduleSeed> collectFscPolicySeeds(YearMonth month) {
        RealEstateExternalFetchResult result = fetchSafely(FSC_PRESS_LIST_URL);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        List<ScheduleSeed> seeds = new ArrayList<>();
        for (String block : htmlBlocks(result.body())) {
            Matcher linkMatcher = LINK_PATTERN.matcher(block);
            while (linkMatcher.find()) {
                String href = HtmlUtils.htmlUnescape(linkMatcher.group(1)).trim();
                String title = cleanHtml(linkMatcher.group(2));
                if (!href.contains("/no010101/") || !isRelevantFinancePolicyTitle(title)) {
                    continue;
                }

                LocalDate publishedDate = firstDateInMonth(dateStrings(block), month);
                if (publishedDate == null) {
                    continue;
                }

                String linkUrl = absoluteUrl(FSC_PRESS_LIST_URL, href);
                String articleId = pathNumberAfter(linkUrl, "/no010101/");
                String idSuffix = isBlank(articleId) ? boardIdSuffix(linkUrl, publishedDate, title) : articleId;
                seeds.add(new ScheduleSeed(
                        "fsc-policy-published-" + idSuffix,
                        "fsc-policy",
                        publishedDate,
                        title,
                        "금융",
                        "금융위원회 부동산 금융정책 보도자료: " + title,
                        "finance",
                        linkUrl,
                        ScheduleSeedKind.PUBLISHED
                ));
                break;
            }
        }
        return seeds;
    }

    private List<ScheduleSeed> collectRealtyPriceNoticeSeeds(YearMonth month) {
        RealEstateExternalFetchResult result = fetchSafely(REALTY_PRICE_BOARD_URL);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        List<ScheduleSeed> seeds = new ArrayList<>();
        for (String block : htmlBlocks(result.body())) {
            Matcher linkMatcher = LINK_PATTERN.matcher(block);
            while (linkMatcher.find()) {
                String href = HtmlUtils.htmlUnescape(linkMatcher.group(1)).trim();
                String title = cleanHtml(linkMatcher.group(2));
                if (isBlank(title) || !isRelevantOfficialPriceTitle(title)) {
                    continue;
                }

                LocalDate publishedDate = firstDateInMonth(dateStrings(block), month);
                if (publishedDate == null) {
                    continue;
                }

                String detailSeq = realtyPriceDetailSeq(href);
                String linkUrl = isBlank(detailSeq)
                        ? absoluteUrl(REALTY_PRICE_BOARD_URL, href)
                        : REALTY_PRICE_DETAIL_URL + "?seq=" + detailSeq;
                if (isListOnlyUrl(REALTY_PRICE_BOARD_URL, linkUrl)) {
                    continue;
                }
                String idSuffix = isBlank(detailSeq) ? boardIdSuffix(linkUrl, publishedDate, title) : detailSeq;
                seeds.add(new ScheduleSeed(
                        "realty-price-published-" + idSuffix,
                        "realty-price",
                        publishedDate,
                        title,
                        "공시가격",
                        "부동산공시가격 알리미 공식 공지: " + title,
                        "market",
                        linkUrl,
                        ScheduleSeedKind.PUBLISHED
                ));
                break;
            }
        }
        return seeds;
    }

    private List<ScheduleSeed> collectBokRateScheduleSeeds(YearMonth month) {
        RealEstateExternalFetchResult result = fetchSafely(BOK_RATE_SCHEDULE_URL);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        Set<LocalDate> dates = new LinkedHashSet<>();
        Matcher rowMatcher = TABLE_ROW_PATTERN.matcher(result.body());
        while (rowMatcher.find()) {
            String rowText = cleanHtml(rowMatcher.group(2));
            Matcher dateMatcher = KOREAN_MONTH_DAY_PATTERN.matcher(rowText);
            if (!dateMatcher.find()) {
                continue;
            }
            int eventMonth = Integer.parseInt(dateMatcher.group(1));
            int eventDay = Integer.parseInt(dateMatcher.group(2));
            if (eventMonth != month.getMonthValue()) {
                continue;
            }
            dates.add(LocalDate.of(month.getYear(), eventMonth, eventDay));
        }

        return dates.stream()
                .map(date -> new ScheduleSeed(
                        "bok-rate-meeting-" + date,
                        "bok-rate",
                        date,
                        "한국은행 통화정책방향 결정회의",
                        "금융",
                        date + " 기준금리와 통화정책방향을 확인하는 한국은행 공식 회의 일정입니다.",
                        "finance",
                        BOK_RATE_SCHEDULE_URL,
                        ScheduleSeedKind.OFFICIAL_SCHEDULE
                ))
                .toList();
    }

    private List<ScheduleSeed> collectBokStatScheduleSeeds(YearMonth month) {
        String scheduleUrl = bokStatScheduleUrl(month);
        RealEstateExternalFetchResult result = fetchSafely(scheduleUrl);
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return List.of();
        }

        List<ScheduleSeed> seeds = new ArrayList<>();
        Matcher rowMatcher = TABLE_ROW_PATTERN.matcher(result.body());
        while (rowMatcher.find()) {
            List<String> cells = tableCells(rowMatcher.group(2));
            if (cells.size() < 3) {
                continue;
            }
            LocalDate scheduleDate = parseDate(cells.get(0));
            String publishTime = cells.get(1);
            String title = cells.get(2);
            if (scheduleDate == null || !YearMonth.from(scheduleDate).equals(month) || !isRelevantBokStatTitle(title)) {
                continue;
            }

            seeds.add(new ScheduleSeed(
                    "bok-stat-schedule-" + Integer.toUnsignedString((scheduleDate + ":" + publishTime + ":" + title).hashCode(), 36),
                    "bok-stat",
                    scheduleDate,
                    title + " 공표 예정",
                    "금융",
                    "한국은행 월간통계 공표일정 기준 " + scheduleDate + " " + publishTime + " 공개 예정인 금융·거시 통계입니다.",
                    "finance",
                    scheduleUrl,
                    ScheduleSeedKind.OFFICIAL_SCHEDULE
            ));
        }
        return seeds;
    }

    private String scheduleStatus(ScheduleSeed seed, SourceCheck check) {
        if (seed.kind() == ScheduleSeedKind.PUBLISHED) {
            return "공표 확인";
        }
        if (check == null || check.stale()) {
            return "출처 확인 필요";
        }
        return "공식 일정";
    }

    private String scheduleDataStatus(ScheduleSeed seed, SourceCheck check) {
        if (seed.kind() == ScheduleSeedKind.PUBLISHED) {
            return "published";
        }
        if (check == null || check.stale()) {
            return "source_error";
        }
        return "scheduled";
    }

    private boolean scheduleStale(ScheduleSeed seed, SourceCheck check) {
        return seed.kind() != ScheduleSeedKind.PUBLISHED && (check == null || check.stale());
    }

    private RealEstateExternalFetchResult fetchSafely(String url) {
        try {
            return fetchClient.fetch(url);
        } catch (RuntimeException ex) {
            return RealEstateExternalFetchResult.failed(0, ex.getMessage());
        }
    }

    private RealEstateExternalFetchResult postFormSafely(String url, Map<String, String> form, Map<String, String> headers) {
        try {
            return fetchClient.postForm(url, form, headers);
        } catch (RuntimeException ex) {
            return RealEstateExternalFetchResult.failed(0, ex.getMessage());
        }
    }

    private static boolean isRelevantMolitPolicy(String field, String title) {
        if (MOLIT_RELEVANT_FIELDS.contains(field)) {
            return true;
        }
        return MOLIT_RELEVANT_TITLE_TERMS.stream().anyMatch(title::contains);
    }

    private static boolean isRelevantMolitStat(String title) {
        return MOLIT_STAT_RELEVANT_TITLE_TERMS.stream().anyMatch(title::contains);
    }

    private static boolean isRelevantRebOfficialSchedule(String title) {
        return title.contains("주택가격")
                || title.contains("아파트가격")
                || title.contains("오피스텔가격")
                || title.contains("공동주택실거래가격지수")
                || title.contains("부동산거래");
    }

    private static String rebScheduleCategory(String title) {
        if (title.contains("부동산거래")) {
            return "거래현황";
        }
        if (title.contains("오피스텔")) {
            return "가격지수";
        }
        if (title.contains("실거래가격지수")) {
            return "가격지수";
        }
        return "가격지수";
    }

    private static String rebScheduleTone(String title) {
        if (title.contains("부동산거래")) {
            return "deal";
        }
        return "market";
    }

    private static boolean isRelevantHugTitle(String title) {
        return HUG_RELEVANT_TITLE_TERMS.stream().anyMatch(title::contains);
    }

    private static boolean isRelevantPublicSupplyTitle(String title) {
        String compactTitle = title.replace(" ", "");
        boolean housingSupply = PUBLIC_SUPPLY_RELEVANT_TITLE_TERMS.stream().anyMatch(title::contains);
        if (!housingSupply) {
            return false;
        }
        boolean nonHousingSupply = compactTitle.contains("상가")
                || compactTitle.contains("토지")
                || compactTitle.contains("산업단지")
                || compactTitle.contains("용지")
                || compactTitle.contains("채용")
                || compactTitle.contains("입찰");
        return !nonHousingSupply || compactTitle.contains("주택");
    }

    private static boolean isRelevantLhPublicSupplyTitle(String title) {
        String compactTitle = title.replace(" ", "");
        if (Set.of("분양주택", "임대주택", "공공분양", "공공임대", "공급공고").contains(compactTitle)) {
            return false;
        }
        if (LH_LOW_SIGNAL_TITLE_TERMS.stream().map(term -> term.replace(" ", "")).anyMatch(compactTitle::contains)) {
            return false;
        }
        return LH_MAJOR_SUPPLY_TITLE_TERMS.stream().anyMatch(title::contains);
    }

    private static boolean isRelevantFinancePolicyTitle(String title) {
        String upperTitle = title.toUpperCase();
        return FINANCE_POLICY_RELEVANT_TITLE_TERMS.stream()
                .anyMatch(term -> upperTitle.contains(term.toUpperCase()));
    }

    private static boolean isRelevantBokStatTitle(String title) {
        return BOK_STAT_RELEVANT_TITLE_TERMS.stream().anyMatch(title::contains);
    }

    private static boolean isRelevantOfficialPriceTitle(String title) {
        return title.contains("공동주택가격")
                || (title.contains("공동주택") && OFFICIAL_PRICE_RELEVANT_TITLE_TERMS.stream().anyMatch(title::contains));
    }

    private static List<String> htmlBlocks(String body) {
        LinkedHashSet<String> blocks = new LinkedHashSet<>();
        Matcher rowMatcher = TABLE_ROW_PATTERN.matcher(body);
        while (rowMatcher.find()) {
            blocks.add(rowMatcher.group(2));
        }
        Matcher itemMatcher = LIST_ITEM_PATTERN.matcher(body);
        while (itemMatcher.find()) {
            blocks.add(itemMatcher.group(1));
        }
        if (blocks.isEmpty()) {
            blocks.add(body);
        }
        return new ArrayList<>(blocks);
    }

    private static String firstRelevantText(String block, List<String> relevantTerms) {
        Matcher linkMatcher = LINK_PATTERN.matcher(block);
        while (linkMatcher.find()) {
            String candidate = cleanHtml(linkMatcher.group(2));
            if (!isBlank(candidate) && relevantTerms.stream().anyMatch(candidate::contains)) {
                return candidate;
            }
        }

        Matcher cellMatcher = TABLE_CELL_PATTERN.matcher(block);
        while (cellMatcher.find()) {
            String candidate = cleanHtml(cellMatcher.group(1));
            if (!isBlank(candidate) && relevantTerms.stream().anyMatch(candidate::contains)) {
                return candidate;
            }
        }

        String text = cleanHtml(block);
        return relevantTerms.stream().anyMatch(text::contains) ? text : "";
    }

    private static String lhPublicSupplyDetailUrl(String block) {
        String panId = attribute(block, "data-id1");
        if (isBlank(panId)) {
            return "";
        }
        StringBuilder detailUrl = new StringBuilder(LH_PUBLIC_DETAIL_URL)
                .append("?panId=")
                .append(panId);
        appendQueryParam(detailUrl, "ccrCnntSysDsCd", attribute(block, "data-id2"));
        appendQueryParam(detailUrl, "uppAisTpCd", attribute(block, "data-id3"));
        appendQueryParam(detailUrl, "aisTpCd", attribute(block, "data-id4"));
        return detailUrl.toString();
    }

    private static void appendQueryParam(StringBuilder url, String name, String value) {
        if (!isBlank(value)) {
            url.append('&').append(name).append('=').append(value);
        }
    }

    private static boolean isPlaceholderHref(String href) {
        if (isBlank(href)) {
            return true;
        }
        String normalized = href.trim().toLowerCase();
        return normalized.startsWith("#")
                || normalized.equals("javascript:void(0)")
                || normalized.equals("javascript:void(0);")
                || normalized.equals("javascript:;");
    }

    private static boolean isListOnlyUrl(String sourceUrl, String linkUrl) {
        URI source = URI.create(sourceUrl);
        URI link = URI.create(linkUrl);
        return source.getHost().equals(link.getHost())
                && source.getPath().equals(link.getPath())
                && isBlank(link.getRawQuery())
                && isBlank(link.getFragment());
    }

    private static String boardIdSuffix(String linkUrl, LocalDate publishedDate, String title) {
        for (String name : List.of("seq", "articleNo", "bbscttSn", "nttSn", "no", "id")) {
            String value = queryParam(linkUrl, name);
            if (!isBlank(value)) {
                return value;
            }
        }

        Matcher lastNumberMatcher = Pattern.compile("(\\d+)(?!.*\\d)").matcher(URI.create(linkUrl).getPath());
        if (lastNumberMatcher.find()) {
            return lastNumberMatcher.group(1);
        }
        return Integer.toUnsignedString((publishedDate + ":" + title + ":" + linkUrl).hashCode(), 36);
    }

    private static String pathNumberAfter(String url, String segment) {
        Matcher matcher = Pattern.compile(Pattern.quote(segment) + "(\\d+)").matcher(url);
        return matcher.find() ? matcher.group(1) : "";
    }

    private static String realtyPriceDetailSeq(String href) {
        Matcher matcher = REALTY_PRICE_DETAIL_PATTERN.matcher(href);
        return matcher.find() ? matcher.group(1) : "";
    }

    private static String classCell(String row, String className) {
        Pattern pattern = Pattern.compile("(?is)<td\\b[^>]*class=\"[^\"]*\\b" + className + "\\b[^\"]*\"[^>]*>(.*?)</td>");
        Matcher matcher = pattern.matcher(row);
        return matcher.find() ? matcher.group(1) : "";
    }

    private static List<String> tableCells(String row) {
        List<String> cells = new ArrayList<>();
        Matcher cellMatcher = TABLE_CELL_PATTERN.matcher(row);
        while (cellMatcher.find()) {
            String value = cleanHtml(cellMatcher.group(1));
            if (!value.isBlank()) {
                cells.add(value);
            }
        }
        return cells;
    }

    private static String attribute(String attributes, String name) {
        Pattern pattern = Pattern.compile("(?is)\\b" + name + "\\s*=\\s*\"([^\"]*)\"");
        Matcher matcher = pattern.matcher(attributes);
        return matcher.find() ? HtmlUtils.htmlUnescape(matcher.group(1)).trim() : "";
    }

    private static List<String> dateStrings(String value) {
        LinkedHashSet<String> dates = new LinkedHashSet<>();
        Matcher isoMatcher = ISO_DATE_PATTERN.matcher(value);
        while (isoMatcher.find()) {
            dates.add(isoMatcher.group());
        }
        Matcher dotMatcher = DOT_DATE_PATTERN.matcher(value);
        while (dotMatcher.find()) {
            dates.add(normalizedDate(dotMatcher.group(1), dotMatcher.group(2), dotMatcher.group(3)));
        }
        Matcher shortDotMatcher = SHORT_DOT_DATE_PATTERN.matcher(value);
        while (shortDotMatcher.find()) {
            dates.add(normalizedDate("20" + shortDotMatcher.group(1), shortDotMatcher.group(2), shortDotMatcher.group(3)));
        }
        return new ArrayList<>(dates);
    }

    private static LocalDate firstDateInMonth(List<String> values, YearMonth month) {
        for (String value : values) {
            LocalDate date = parseDate(value);
            if (date != null && YearMonth.from(date).equals(month)) {
                return date;
            }
        }
        return null;
    }

    private static LocalDate parseDate(String value) {
        if (isBlank(value)) {
            return null;
        }
        Matcher matcher = ISO_DATE_PATTERN.matcher(value);
        if (!matcher.find()) {
            return null;
        }
        return LocalDate.parse(matcher.group());
    }

    private static LocalDate parseCompactDate(String value) {
        if (isBlank(value) || value.length() != 8) {
            return null;
        }
        return LocalDate.of(
                Integer.parseInt(value.substring(0, 4)),
                Integer.parseInt(value.substring(4, 6)),
                Integer.parseInt(value.substring(6, 8))
        );
    }

    private static String normalizedDate(String year, String month, String day) {
        return String.format("%s-%02d-%02d", year, Integer.parseInt(month), Integer.parseInt(day));
    }

    private static String applyHomeSummary(List<String> dates) {
        String noticeDate = dates.getFirst();
        if (dates.size() >= 4) {
            return "모집공고일 " + noticeDate
                    + ", 청약기간 " + dates.get(1) + "~" + dates.get(2)
                    + ", 당첨자 발표 " + dates.get(3)
                    + "인 청약Home 공고입니다.";
        }
        if (dates.size() >= 2) {
            return "모집공고일 " + noticeDate
                    + ", 후속 청약 일정은 " + dates.get(1)
                    + "부터 확인되는 청약Home 공고입니다.";
        }
        return "모집공고일 " + noticeDate + "인 청약Home 공고입니다.";
    }

    private static JsonNode readJson(RealEstateExternalFetchResult result) {
        if (!result.success() || result.body() == null || result.body().isBlank()) {
            return null;
        }
        try {
            return OBJECT_MAPPER.readTree(result.body());
        } catch (RuntimeException ex) {
            return null;
        } catch (Exception ex) {
            return null;
        }
    }

    private static String cleanHtml(String value) {
        if (value == null) {
            return "";
        }
        return HtmlUtils.htmlUnescape(value)
                .replaceAll("(?is)<[^>]+>", " ")
                .replace('\u00a0', ' ')
                .replaceAll("\\s+", " ")
                .trim();
    }

    private static String absoluteUrl(String baseUrl, String href) {
        return URI.create(baseUrl).resolve(href).toString();
    }

    private static String bokStatScheduleUrl(YearMonth month) {
        return "https://www.bok.or.kr/portal/stats/statsPublictSchdul/listCldr.do?date=" + month + "&menuNo=200775";
    }

    private static String queryParam(String url, String name) {
        String query = URI.create(url).getRawQuery();
        if (query == null) {
            return "";
        }
        for (String pair : query.split("&")) {
            int separator = pair.indexOf('=');
            if (separator < 0) {
                continue;
            }
            String key = pair.substring(0, separator);
            if (name.equals(key)) {
                return pair.substring(separator + 1);
            }
        }
        return "";
    }

    private static boolean hasScheduleContextUrl(ScheduleSeed seed) {
        if (isBlank(seed.linkUrl())) {
            return false;
        }
        String url = seed.linkUrl();
        if ("bok-rate".equals(seed.sourceId()) && BOK_RATE_SCHEDULE_URL.equals(url)) {
            return true;
        }
        if ("bok-stat".equals(seed.sourceId()) && url.startsWith("https://www.bok.or.kr/portal/stats/statsPublictSchdul/listCldr.do?date=")) {
            return true;
        }
        return url.contains("selectBulletinPage.do")
                || url.contains("easyStatPage.do?cateId=")
                || url.contains("viewChk.do")
                || url.contains("selectAPTLttotPblancDetail.do")
                || url.contains("selectWrtancInfo.do")
                || url.contains("articleId=")
                || url.contains("/site/main/sh/publicLease/07/view")
                || url.contains("announcement-of-salerental001.do?articleNo=")
                || url.contains("/main/sale_lease/notice_view.jsp")
                || url.contains("/USR/NEWS/")
                || url.contains("/no010101/")
                || url.contains("boardDetailAll.board?seq=");
    }

    private static boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    private MarketDataScheduleEventResponse toEventResponse(MarketDataSchedule schedule) {
        return new MarketDataScheduleEventResponse(
                schedule.getId(),
                schedule.getScheduleDate(),
                schedule.getTitle(),
                schedule.getCategory(),
                schedule.getSourceTitle(),
                schedule.getSummary(),
                schedule.getSourceUrl(),
                schedule.getTone(),
                schedule.getProvider(),
                schedule.getStatus(),
                schedule.getDataStatus(),
                schedule.isStale(),
                schedule.getLastCheckedAt(),
                schedule.getAsOf()
        );
    }

    private MarketDataSourceLinkResponse toSourceResponse(MarketDataSource source) {
        return new MarketDataSourceLinkResponse(
                source.getId(),
                source.getTitle(),
                source.getLabel(),
                source.getSourceUrl(),
                source.getProvider(),
                source.getStatus(),
                source.isStale() ? "error" : "ok",
                source.isStale(),
                source.getLastCheckedAt()
        );
    }

    private record SourceDefinition(
            String id,
            String title,
            String label,
            String provider,
            String url,
            String category,
            String tone
    ) {
    }

    private record ScheduleSeed(
            String id,
            String sourceId,
            LocalDate date,
            String title,
            String category,
            String summary,
            String tone,
            String linkUrl,
            ScheduleSeedKind kind
    ) {
    }

    private enum ScheduleSeedKind {
        PUBLISHED,
        OFFICIAL_SCHEDULE
    }

    private record RebBulletinCategory(
            String code,
            String category,
            String tone
    ) {
    }

    private record SourceCheck(
            String status,
            String dataStatus,
            boolean stale,
            Instant checkedAt
    ) {
    }
}
