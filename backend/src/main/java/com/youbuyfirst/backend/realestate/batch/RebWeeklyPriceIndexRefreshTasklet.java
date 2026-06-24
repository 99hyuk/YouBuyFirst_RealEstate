package com.youbuyfirst.backend.realestate.batch;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.youbuyfirst.backend.realestate.RealEstateMapLayerService;
import com.youbuyfirst.backend.realestate.RealEstateMarketFactService;
import com.youbuyfirst.backend.realestate.RealEstateRegionRepository;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerRefreshRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketFactRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetResponse;
import org.springframework.batch.core.StepContribution;
import org.springframework.batch.core.scope.context.ChunkContext;
import org.springframework.batch.core.step.tasklet.Tasklet;
import org.springframework.batch.repeat.RepeatStatus;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.time.DateTimeException;
import java.time.Instant;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoField;
import java.time.temporal.IsoFields;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
public class RebWeeklyPriceIndexRefreshTasklet implements Tasklet {

    private static final String TOPIC = "map-layers";
    private static final String PROVIDER = "reb";
    private static final String PROVIDER_DATASET = "reb_rone_weekly_apt_sale_price_index_region";
    private static final String FACT_TYPE = "price_index";
    private static final String STATBL_ID = "T244183132827305";
    private static final String DEFAULT_SOURCE_URL = "https://www.reb.or.kr/r-one/portal/stat/easyStatPage/" + STATBL_ID + ".do";
    private static final String DATA_URL = "https://www.reb.or.kr/r-one/portal/stat/sttsDataPreviewList.do";
    private static final String SOURCE_LABEL = "REB R-ONE weekly apartment sale price index";
    private static final List<String> MAP_PERIODS = List.of("week", "month", "quarter", "halfYear", "year");
    private static final Pattern FIR_PARAM_PATTERN = Pattern.compile("id=\"firParam\"[^>]*value=\"([^\"]+)\"");
    private static final Pattern WEEKLY_INDEX_COLUMN_PATTERN = Pattern.compile("^COL_(\\d{6})\\d*OD$");
    private static final Map<String, List<String>> PROVINCE_ALIASES = Map.ofEntries(
            Map.entry("\uC11C\uC6B8", List.of("\uC11C\uC6B8\uD2B9\uBCC4\uC2DC")),
            Map.entry("\uBD80\uC0B0", List.of("\uBD80\uC0B0\uAD11\uC5ED\uC2DC")),
            Map.entry("\uB300\uAD6C", List.of("\uB300\uAD6C\uAD11\uC5ED\uC2DC")),
            Map.entry("\uC778\uCC9C", List.of("\uC778\uCC9C\uAD11\uC5ED\uC2DC")),
            Map.entry("\uAD11\uC8FC", List.of("\uAD11\uC8FC\uAD11\uC5ED\uC2DC")),
            Map.entry("\uB300\uC804", List.of("\uB300\uC804\uAD11\uC5ED\uC2DC")),
            Map.entry("\uC6B8\uC0B0", List.of("\uC6B8\uC0B0\uAD11\uC5ED\uC2DC")),
            Map.entry("\uC138\uC885", List.of("\uC138\uC885\uD2B9\uBCC4\uC790\uCE58\uC2DC")),
            Map.entry("\uACBD\uAE30", List.of("\uACBD\uAE30\uB3C4")),
            Map.entry("\uAC15\uC6D0", List.of("\uAC15\uC6D0\uD2B9\uBCC4\uC790\uCE58\uB3C4", "\uAC15\uC6D0\uB3C4")),
            Map.entry("\uCDA9\uBD81", List.of("\uCDA9\uCCAD\uBD81\uB3C4")),
            Map.entry("\uCDA9\uB0A8", List.of("\uCDA9\uCCAD\uB0A8\uB3C4")),
            Map.entry("\uC804\uBD81", List.of("\uC804\uBD81\uD2B9\uBCC4\uC790\uCE58\uB3C4", "\uC804\uB77C\uBD81\uB3C4")),
            Map.entry("\uC804\uB0A8", List.of("\uC804\uB77C\uB0A8\uB3C4")),
            Map.entry("\uACBD\uBD81", List.of("\uACBD\uC0C1\uBD81\uB3C4")),
            Map.entry("\uACBD\uB0A8", List.of("\uACBD\uC0C1\uB0A8\uB3C4")),
            Map.entry("\uC81C\uC8FC", List.of("\uC81C\uC8FC\uD2B9\uBCC4\uC790\uCE58\uB3C4"))
    );

    private final RealEstateExternalFetchClient fetchClient;
    private final RealEstateMarketFactService marketFactService;
    private final RealEstateMapLayerService mapLayerService;
    private final RealEstateRegionRepository regionRepository;
    private final RealEstateBatchUpdatePublisher updatePublisher;
    private final ObjectMapper objectMapper;
    private final String sourceUrl;
    private final int latestWeeks;

    public RebWeeklyPriceIndexRefreshTasklet(
            RealEstateExternalFetchClient fetchClient,
            RealEstateMarketFactService marketFactService,
            RealEstateMapLayerService mapLayerService,
            RealEstateRegionRepository regionRepository,
            RealEstateBatchUpdatePublisher updatePublisher,
            ObjectMapper objectMapper,
            @Value("${app.realestate.batch.reb-weekly-price-index-url:" + DEFAULT_SOURCE_URL + "}") String sourceUrl,
            @Value("${app.realestate.batch.reb-weekly-price-index-latest-weeks:60}") int latestWeeks
    ) {
        this.fetchClient = fetchClient;
        this.marketFactService = marketFactService;
        this.mapLayerService = mapLayerService;
        this.regionRepository = regionRepository;
        this.updatePublisher = updatePublisher;
        this.objectMapper = objectMapper;
        this.sourceUrl = sourceUrl == null || sourceUrl.isBlank() ? DEFAULT_SOURCE_URL : sourceUrl.trim();
        this.latestWeeks = Math.max(53, latestWeeks);
    }

    @Override
    public RepeatStatus execute(StepContribution contribution, ChunkContext chunkContext) {
        Instant asOf = parseAsOf(chunkContext);
        RealEstateExternalFetchResult result = fetchClient.fetch(sourceUrl);
        if (!result.success()) {
            throw new IllegalStateException("REB weekly price index fetch failed: " + result.statusCode());
        }

        List<RealEstateMarketFactRequest> facts = parseSource(result.body(), asOf);
        int acceptedFacts = marketFactService.upsertAll(facts);
        int acceptedSnapshots = mapLayerService.refreshSnapshots(
                new RealEstateMapLayerRefreshRequest("sido", MAP_PERIODS, asOf)
        ).acceptedSnapshots();
        acceptedSnapshots += mapLayerService.refreshSnapshots(
                new RealEstateMapLayerRefreshRequest("sigungu", MAP_PERIODS, asOf)
        ).acceptedSnapshots();

        int acceptedItems = acceptedFacts + acceptedSnapshots;
        contribution.incrementReadCount();
        contribution.incrementWriteCount(acceptedItems);
        updatePublisher.publish(new RealEstateBatchUpdateEvent(
                TOPIC,
                null,
                acceptedItems,
                Instant.now()
        ));
        return RepeatStatus.FINISHED;
    }

    private Instant parseAsOf(ChunkContext chunkContext) {
        Object raw = chunkContext.getStepContext().getJobParameters().get("asOf");
        if (raw instanceof String value && !value.isBlank()) {
            return Instant.parse(value);
        }
        return Instant.now();
    }

    private List<RealEstateMarketFactRequest> parseSource(String body, Instant ingestedAt) {
        String normalizedBody = body == null ? "" : body.stripLeading();
        if (normalizedBody.startsWith("{")) {
            return parseRoneWeeklyJson(normalizedBody, ingestedAt);
        }
        if (looksLikeCsv(normalizedBody)) {
            return parseCsv(normalizedBody, ingestedAt);
        }
        return parseRoneEasyStatPage(normalizedBody, ingestedAt);
    }

    private List<RealEstateMarketFactRequest> parseRoneEasyStatPage(String html, Instant ingestedAt) {
        Map<String, String> form = parseFirParam(html);
        form.put("statblId", STATBL_ID);
        form.put("dtacycleCd", "WK");
        form.put("dtadvsCd", "OD");
        form.put("wrttimeLastestVal", String.valueOf(latestWeeks));
        form.put("wrttimeOrder", "A");
        RealEstateExternalFetchResult dataResult = fetchClient.postForm(
                DATA_URL,
                form,
                Map.of(
                        "Referer", sourceUrl,
                        "X-Requested-With", "XMLHttpRequest",
                        "Accept", "application/json, text/javascript, */*; q=0.01"
                )
        );
        if (!dataResult.success()) {
            throw new IllegalStateException("REB weekly price index data fetch failed: " + dataResult.statusCode());
        }
        return parseRoneWeeklyJson(dataResult.body(), ingestedAt);
    }

    private Map<String, String> parseFirParam(String html) {
        Matcher matcher = FIR_PARAM_PATTERN.matcher(html == null ? "" : html);
        if (!matcher.find()) {
            throw new IllegalStateException("REB R-ONE weekly page has no firParam");
        }
        String rawQuery = matcher.group(1)
                .replace("&amp;", "&")
                .replace("&#38;", "&");
        Map<String, String> form = new LinkedHashMap<>();
        for (String pair : rawQuery.split("&")) {
            if (pair.isBlank()) {
                continue;
            }
            int separator = pair.indexOf('=');
            String rawKey = separator >= 0 ? pair.substring(0, separator) : pair;
            String rawValue = separator >= 0 ? pair.substring(separator + 1) : "";
            form.put(decodeQueryValue(rawKey), decodeQueryValue(rawValue));
        }
        return form;
    }

    private List<RealEstateMarketFactRequest> parseRoneWeeklyJson(String json, Instant ingestedAt) {
        try {
            JsonNode root = objectMapper.readTree(json);
            JsonNode rows = root.path("DATA");
            if (!rows.isArray()) {
                throw new IllegalStateException("REB weekly price index response has no DATA rows");
            }

            Map<String, TargetMatch> regionLookup = buildRegionLookup();
            List<RealEstateMarketFactRequest> requests = new ArrayList<>();
            Set<String> seenProviderObjectIds = new LinkedHashSet<>();
            for (JsonNode row : rows) {
                String provinceName = text(row.path("CATE1"));
                String regionName = regionName(row);
                if (provinceName.isBlank() || regionName.isBlank() || "\uC804\uAD6D".equals(regionName)) {
                    continue;
                }
                Optional<TargetMatch> target = findTarget(regionLookup, provinceName, regionName);
                if (target.isEmpty()) {
                    continue;
                }
                List<WeeklyIndexValue> values = weeklyIndexValues(row);
                for (WeeklyIndexValue current : values) {
                    RealEstateMarketFactRequest request = weeklyMarketFactRequest(
                            provinceName,
                            regionName,
                            target.get(),
                            current,
                            ingestedAt
                    );
                    if (seenProviderObjectIds.add(request.providerObjectId())) {
                        requests.add(request);
                    }
                }
            }
            if (requests.isEmpty()) {
                throw new IllegalStateException("REB weekly price index response contained no mapped regional index rows");
            }
            return requests;
        } catch (Exception exc) {
            if (exc instanceof IllegalStateException illegalStateException) {
                throw illegalStateException;
            }
            throw new IllegalStateException("REB weekly price index response is not supported JSON", exc);
        }
    }

    private RealEstateMarketFactRequest weeklyMarketFactRequest(
            String provinceName,
            String regionName,
            TargetMatch target,
            WeeklyIndexValue current,
            Instant ingestedAt
    ) {
        ObjectNode value = objectMapper.createObjectNode();
        value.put("value", current.value());
        value.put("indexValue", current.value());
        value.put("unit", "지수");
        value.put("metricCode", "reb_weekly_apt_sale_price_index_region");
        value.put("metricName", "R-ONE weekly apartment sale price index");
        value.put("frequency", "weekly");
        value.put("housingScope", "apartment");
        value.put("dimension", "region");
        value.put("sourceStatblId", STATBL_ID);
        value.put("sourceLabel", SOURCE_LABEL);
        value.put("sourceUrl", sourceUrl);
        value.put("provinceName", provinceName);
        value.put("regionName", regionName);
        value.put("targetDisplayName", target.displayName());
        value.put("periodWeek", current.periodKey());
        value.put("sourceIndexProvided", true);
        value.put("sampleCount", 1);
        value.put("confidence", 1.0);

        LocalDate observedAt = observedAtFromWeekKey(current.periodKey());
        return new RealEstateMarketFactRequest(
                "region",
                target.targetId(),
                FACT_TYPE,
                PROVIDER,
                PROVIDER_DATASET,
                providerObjectId(current.periodKey(), target.legalDongCode()),
                target.legalDongCode(),
                observedAt,
                observedAt,
                ingestedAt,
                null,
                value,
                "ok",
                false
        );
    }

    private Map<String, TargetMatch> buildRegionLookup() {
        Map<String, TargetMatch> lookup = new HashMap<>();
        for (RealEstateTargetResponse target : regionRepository.listTargets(null, Pageable.unpaged())) {
            if (!"region".equals(target.targetType()) || target.legalDongCode() == null || target.legalDongCode().isBlank()) {
                continue;
            }
            TargetMatch match = new TargetMatch(target.targetId(), target.legalDongCode(), target.displayName());
            addLookupName(lookup, target.displayName(), match);
            for (Map.Entry<String, List<String>> provinceEntry : PROVINCE_ALIASES.entrySet()) {
                for (String fullProvinceName : provinceEntry.getValue()) {
                    if (target.displayName().equals(fullProvinceName)) {
                        addLookupName(lookup, provinceEntry.getKey(), match);
                    }
                    String prefix = fullProvinceName + " ";
                    if (target.displayName().startsWith(prefix)) {
                        String suffix = target.displayName().substring(prefix.length());
                        addLookupName(lookup, provinceEntry.getKey() + " " + suffix, match);
                        addLookupName(lookup, provinceEntry.getKey() + suffix, match);
                    }
                }
            }
        }
        return lookup;
    }

    private static void addLookupName(Map<String, TargetMatch> lookup, String name, TargetMatch match) {
        String key = normalizeName(name);
        if (!key.isBlank()) {
            lookup.putIfAbsent(key, match);
        }
    }

    private static Optional<TargetMatch> findTarget(
            Map<String, TargetMatch> lookup,
            String provinceName,
            String regionName
    ) {
        for (String candidate : targetNameCandidates(provinceName, regionName)) {
            TargetMatch match = lookup.get(normalizeName(candidate));
            if (match != null) {
                return Optional.of(match);
            }
        }
        return Optional.empty();
    }

    private static List<String> targetNameCandidates(String provinceName, String regionName) {
        LinkedHashSet<String> candidates = new LinkedHashSet<>();
        candidates.add(regionName);
        candidates.add(provinceName + " " + regionName);
        candidates.add(provinceName + regionName);
        for (String fullProvinceName : PROVINCE_ALIASES.getOrDefault(provinceName, List.of(provinceName))) {
            candidates.add(fullProvinceName + " " + regionName);
            candidates.add(fullProvinceName + regionName);
            if (provinceName.equals(regionName)) {
                candidates.add(fullProvinceName);
            }
        }
        candidates.add(provinceName);
        candidates.addAll(PROVINCE_ALIASES.getOrDefault(provinceName, List.of(provinceName)));
        return new ArrayList<>(candidates);
    }

    private static String regionName(JsonNode row) {
        for (String key : List.of("CATE4", "CATE3", "CATE2", "CATE1")) {
            String value = text(row.path(key));
            if (!value.isBlank()) {
                return value;
            }
        }
        return "";
    }

    private static List<WeeklyIndexValue> weeklyIndexValues(JsonNode row) {
        List<WeeklyIndexValue> values = new ArrayList<>();
        row.fields().forEachRemaining(entry -> {
            Matcher matcher = WEEKLY_INDEX_COLUMN_PATTERN.matcher(entry.getKey());
            if (matcher.matches()) {
                parseDecimal(text(entry.getValue()))
                        .ifPresent(value -> values.add(new WeeklyIndexValue(matcher.group(1), value)));
            }
        });
        return values;
    }

    private static Optional<BigDecimal> parseDecimal(String value) {
        if (value == null || value.isBlank() || "-".equals(value.trim())) {
            return Optional.empty();
        }
        try {
            return Optional.of(new BigDecimal(value.replace(",", "").trim()));
        } catch (NumberFormatException exc) {
            return Optional.empty();
        }
    }

    private static LocalDate observedAtFromWeekKey(String periodKey) {
        int year = Integer.parseInt(periodKey.substring(0, 4));
        int week = Integer.parseInt(periodKey.substring(4, 6));
        try {
            return LocalDate.of(year, 1, 4)
                    .with(IsoFields.WEEK_OF_WEEK_BASED_YEAR, week)
                    .with(ChronoField.DAY_OF_WEEK, 4);
        } catch (DateTimeException exc) {
            return LocalDate.of(year, 1, 1).plusWeeks(Math.max(0, week - 1L));
        }
    }

    private List<RealEstateMarketFactRequest> parseCsv(String body, Instant ingestedAt) {
        if (body == null || body.isBlank()) {
            return List.of();
        }
        String[] lines = body.replace("\r\n", "\n").replace('\r', '\n').split("\n");
        if (lines.length < 2) {
            return List.of();
        }
        List<String> headerCells = parseCsvLine(lines[0]);
        Map<String, Integer> header = new HashMap<>();
        for (int index = 0; index < headerCells.size(); index++) {
            header.put(normalizeColumnName(headerCells.get(index)), index);
        }

        List<RealEstateMarketFactRequest> requests = new ArrayList<>();
        for (int lineIndex = 1; lineIndex < lines.length; lineIndex++) {
            if (lines[lineIndex].isBlank()) {
                continue;
            }
            List<String> row = parseCsvLine(lines[lineIndex]);
            Optional<RealEstateMarketFactRequest> request = toMarketFactRequest(header, row, ingestedAt);
            request.ifPresent(requests::add);
        }
        return requests;
    }

    private Optional<RealEstateMarketFactRequest> toMarketFactRequest(
            Map<String, Integer> header,
            List<String> row,
            Instant ingestedAt
    ) {
        String legalDongCode = column(header, row, "legalDongCode", "legalCode", "lawdCd");
        String observedAtValue = column(header, row, "observedAt", "date", "baseDate", "weekDate");
        String indexValueText = column(header, row, "indexValue", "priceIndex", "value", "index");
        if (legalDongCode.isBlank() || observedAtValue.isBlank() || indexValueText.isBlank()) {
            return Optional.empty();
        }

        LocalDate observedAt = LocalDate.parse(observedAtValue.trim());
        BigDecimal indexValue = new BigDecimal(indexValueText.replace(",", "").trim());
        String targetId = column(header, row, "targetId", "target");
        String regionName = column(header, row, "regionName", "name", "region");
        Instant sourceUpdatedAt = parseInstant(column(header, row, "sourceUpdatedAt", "updatedAt"))
                .orElse(null);

        ObjectNode value = objectMapper.createObjectNode();
        value.put("value", indexValue);
        value.put("indexValue", indexValue);
        value.put("unit", "지수");
        value.put("metricCode", "reb_weekly_apt_sale_price_index_region");
        value.put("metricName", "R-ONE weekly apartment sale price index");
        value.put("frequency", "weekly");
        value.put("housingScope", "apartment");
        value.put("dimension", "region");
        value.put("sourceStatblId", STATBL_ID);
        value.put("sourceLabel", SOURCE_LABEL);
        value.put("sourceUrl", sourceUrl);
        value.put("sourceIndexProvided", true);
        value.put("sampleCount", 1);
        value.put("confidence", 1.0);
        if (!regionName.isBlank()) {
            value.put("regionName", regionName);
        }

        return Optional.of(new RealEstateMarketFactRequest(
                "region",
                targetId.isBlank() ? null : targetId,
                FACT_TYPE,
                PROVIDER,
                PROVIDER_DATASET,
                providerObjectId(observedAt, legalDongCode),
                legalDongCode.trim(),
                observedAt,
                observedAt,
                ingestedAt,
                sourceUpdatedAt,
                value,
                "ok",
                false
        ));
    }

    private static String providerObjectId(LocalDate observedAt, String legalDongCode) {
        return providerObjectId(DateTimeFormatter.BASIC_ISO_DATE.format(observedAt), legalDongCode);
    }

    private static String providerObjectId(String periodKey, String legalDongCode) {
        return "%s:%s:%s:%s".formatted(
                PROVIDER_DATASET,
                STATBL_ID,
                periodKey,
                legalDongCode.trim()
        );
    }

    private static Optional<Instant> parseInstant(String value) {
        if (value == null || value.isBlank()) {
            return Optional.empty();
        }
        return Optional.of(Instant.parse(value.trim()));
    }

    private static String column(Map<String, Integer> header, List<String> row, String... names) {
        for (String name : names) {
            Integer index = header.get(normalizeColumnName(name));
            if (index != null && index >= 0 && index < row.size()) {
                return row.get(index).trim();
            }
        }
        return "";
    }

    private static String normalizeColumnName(String value) {
        return normalizeName(value);
    }

    private static String normalizeName(String value) {
        if (value == null) {
            return "";
        }
        StringBuilder normalized = new StringBuilder();
        value.toLowerCase(Locale.ROOT).codePoints()
                .filter(Character::isLetterOrDigit)
                .forEach(normalized::appendCodePoint);
        return normalized.toString();
    }

    private static List<String> parseCsvLine(String line) {
        List<String> cells = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        boolean quoted = false;
        for (int index = 0; index < line.length(); index++) {
            char ch = line.charAt(index);
            if (ch == '"') {
                if (quoted && index + 1 < line.length() && line.charAt(index + 1) == '"') {
                    current.append('"');
                    index++;
                } else {
                    quoted = !quoted;
                }
            } else if (ch == ',' && !quoted) {
                cells.add(current.toString());
                current.setLength(0);
            } else {
                current.append(ch);
            }
        }
        cells.add(current.toString());
        return cells;
    }

    private static boolean looksLikeCsv(String body) {
        String firstLine = body == null ? "" : body.lines().findFirst().orElse("");
        String normalized = normalizeColumnName(firstLine);
        return normalized.contains("legaldongcode") || normalized.contains("observedat");
    }

    private static String decodeQueryValue(String value) {
        return URLDecoder.decode(value == null ? "" : value, StandardCharsets.UTF_8);
    }

    private static String text(JsonNode node) {
        if (node == null || node.isMissingNode() || node.isNull()) {
            return "";
        }
        return node.asText("").trim();
    }

    private record TargetMatch(String targetId, String legalDongCode, String displayName) {
    }

    private record WeeklyIndexValue(String periodKey, BigDecimal value) {
    }
}
