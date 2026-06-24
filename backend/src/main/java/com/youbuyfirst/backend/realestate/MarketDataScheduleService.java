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
    private static final String MOLIT_POLICY_LIST_URL = "https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp";
    private static final String MOLIT_STAT_SCHEDULE_URL = "https://stat.molit.go.kr/portal/notice/scheduleList.do";
    private static final String APPLYHOME_APT_LIST_URL = "https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancListView.do";
    private static final String APPLYHOME_APT_DETAIL_URL = "https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancDetail.do";
    private static final String BOK_RATE_SCHEDULE_URL = "https://www.bok.or.kr/portal/singl/crncyPolicyDrcMtg/listYear.do?menuNo=200755&mtgSe=A";
    private static final Pattern TABLE_ROW_PATTERN = Pattern.compile("(?is)<tr\\b([^>]*)>(.*?)</tr>");
    private static final Pattern MOLIT_TITLE_LINK_PATTERN = Pattern.compile("(?is)<td\\b[^>]*class=\"[^\"]*\\bbd_title\\b[^\"]*\"[^>]*>.*?<a\\b[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>");
    private static final Pattern LINK_PATTERN = Pattern.compile("(?is)<a\\b[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>");
    private static final Pattern ISO_DATE_PATTERN = Pattern.compile("\\d{4}-\\d{2}-\\d{2}");
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
    private static final List<RebBulletinCategory> REB_BULLETIN_CATEGORIES = List.of(
            new RebBulletinCategory("PRES01", "가격지수", "market"),
            new RebBulletinCategory("PRES02", "가격지수", "market"),
            new RebBulletinCategory("PRES05", "가격지수", "market"),
            new RebBulletinCategory("PRES06", "전세", "deal"),
            new RebBulletinCategory("PRES07", "실거래", "deal")
    );

    private static final List<SourceDefinition> SOURCES = List.of(
            new SourceDefinition("reb-r-one", "한국부동산원 R-ONE", "가격지수·공표일정", "reb", "https://www.reb.or.kr/r-one/portal/main/indexPage.do", "가격지수", "market"),
            new SourceDefinition("rt-molit", "국토교통부 실거래가 공개시스템", "매매·전월세 거래", "molit", "https://rt.molit.go.kr/", "실거래", "deal"),
            new SourceDefinition("molit-stat", "국토교통 통계누리", "미분양·공급", "molit", "https://stat.molit.go.kr/", "공급", "supply"),
            new SourceDefinition("bok-rate", "한국은행 일정", "금리·통화정책", "bok", BOK_RATE_SCHEDULE_URL, "금융", "finance"),
            new SourceDefinition("applyhome", "청약Home", "청약·분양", "applyhome", "https://applyhome.co.kr/", "청약", "subscription"),
            new SourceDefinition("molit-policy", "국토교통부", "정책·보도자료", "molit", "https://www.molit.go.kr/", "정책", "policy"),
            new SourceDefinition("hug-market", "HUG 주택도시보증공사", "보증·주택시장", "hug", "https://www.khug.or.kr/", "보증", "supply")
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
        List<ScheduleSeed> seeds = scheduleSeeds(month);
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
        return seeds;
    }

    private List<ScheduleSeed> collectOfficialScheduleSeeds(YearMonth month) {
        List<ScheduleSeed> seeds = new ArrayList<>();
        seeds.addAll(collectMolitStatScheduleSeeds(month));
        seeds.addAll(collectBokRateScheduleSeeds(month));
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
            if (noticeDate == null || !YearMonth.from(noticeDate).equals(month)) {
                continue;
            }

            seeds.add(new ScheduleSeed(
                    "applyhome-published-" + pblancNo,
                    "applyhome",
                    noticeDate,
                    houseName + " 입주자모집공고",
                    "청약",
                    applyHomeSummary(dates),
                    "subscription",
                    APPLYHOME_APT_DETAIL_URL + "?houseManageNo=" + houseManageNo + "&pblancNo=" + pblancNo,
                    ScheduleSeedKind.PUBLISHED
            ));
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

    private static String classCell(String row, String className) {
        Pattern pattern = Pattern.compile("(?is)<td\\b[^>]*class=\"[^\"]*\\b" + className + "\\b[^\"]*\"[^>]*>(.*?)</td>");
        Matcher matcher = pattern.matcher(row);
        return matcher.find() ? matcher.group(1) : "";
    }

    private static String attribute(String attributes, String name) {
        Pattern pattern = Pattern.compile("(?is)\\b" + name + "\\s*=\\s*\"([^\"]*)\"");
        Matcher matcher = pattern.matcher(attributes);
        return matcher.find() ? HtmlUtils.htmlUnescape(matcher.group(1)).trim() : "";
    }

    private static List<String> dateStrings(String value) {
        List<String> dates = new ArrayList<>();
        Matcher matcher = ISO_DATE_PATTERN.matcher(value);
        while (matcher.find()) {
            dates.add(matcher.group());
        }
        return dates;
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
