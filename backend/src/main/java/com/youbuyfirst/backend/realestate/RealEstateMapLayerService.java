package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.indicator.RealEstateReactionSnapshot;
import com.youbuyfirst.backend.indicator.RealEstateReactionSnapshotRepository;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerPeriodResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerRefreshRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerRefreshResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerTargetResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;

@Service
public class RealEstateMapLayerService {

    private static final List<String> PERIOD_ORDER = List.of("week", "month", "quarter", "halfYear", "year");
    private static final String MAP_REFRESH_PROVIDER = "real_estate_map_layer_refresh";
    private static final String MAP_REFRESH_SOURCE_LABEL = "실거래 market facts + 반응 snapshot";
    private static final String REACTION_ONLY_PROVIDER = "real_estate_reaction_snapshots";
    private static final String REACTION_ONLY_SOURCE_LABEL = "커뮤니티 반응 heat · market fact 수집 전";
    private static final String OFFICIAL_PRICE_INDEX_FACT_TYPE = "price_index";
    private static final String OFFICIAL_PRICE_INDEX_WEEKLY_DATASET = "reb_rone_weekly_apt_sale_price_index_region";
    private static final String OFFICIAL_PRICE_INDEX_MONTHLY_DATASET = "reb_rone_monthly_apt_sale_price_index";
    private static final List<String> OFFICIAL_PRICE_INDEX_WEEKLY_PROVIDER_DATASETS = List.of(
            OFFICIAL_PRICE_INDEX_WEEKLY_DATASET
    );
    private static final List<String> OFFICIAL_PRICE_INDEX_MONTHLY_PROVIDER_DATASETS = List.of(
            OFFICIAL_PRICE_INDEX_MONTHLY_DATASET
    );
    private static final String OFFICIAL_PRICE_INDEX_SOURCE_LABEL =
            "한국부동산원 R-ONE 전국주택가격동향조사 매매가격지수";
    private static final BigDecimal EXTREME_CHANGE_THRESHOLD_PCT = BigDecimal.valueOf(50);
    private static final Map<String, String> RONE_MONTHLY_SINGLE_TIER_LEGAL_DONG_CODES_BY_REGION_CODE = Map.of(
            "29010", "36"
    );
    private static final Map<String, String> RONE_WEEKLY_SINGLE_TIER_LEGAL_DONG_CODES_BY_REGION_CODE = Map.of(
            "29010", "36000"
    );
    private static final Map<String, String> RONE_WEEKLY_SIDO_LEGAL_DONG_CODES_BY_REGION_CODE = Map.ofEntries(
            Map.entry("11", "11000"),
            Map.entry("21", "26000"),
            Map.entry("22", "27000"),
            Map.entry("23", "28000"),
            Map.entry("24", "29000"),
            Map.entry("25", "30000"),
            Map.entry("26", "31000"),
            Map.entry("29", "36000"),
            Map.entry("31", "41000"),
            Map.entry("32", "42000"),
            Map.entry("33", "43000"),
            Map.entry("34", "44000"),
            Map.entry("35", "45000"),
            Map.entry("36", "46000"),
            Map.entry("37", "47000"),
            Map.entry("38", "48000"),
            Map.entry("39", "50000")
    );

    private final MapFeatureRepository mapFeatureRepository;
    private final MapLayerSnapshotRepository mapLayerSnapshotRepository;
    private final RealEstateMarketFactRepository marketFactRepository;
    private final RealEstateReactionSnapshotRepository reactionSnapshotRepository;
    private final RealEstateRegionRepository regionRepository;
    private final ObjectMapper objectMapper;

    public RealEstateMapLayerService(
            MapFeatureRepository mapFeatureRepository,
            MapLayerSnapshotRepository mapLayerSnapshotRepository,
            RealEstateMarketFactRepository marketFactRepository,
            RealEstateReactionSnapshotRepository reactionSnapshotRepository,
            RealEstateRegionRepository regionRepository,
            ObjectMapper objectMapper
    ) {
        this.mapFeatureRepository = mapFeatureRepository;
        this.mapLayerSnapshotRepository = mapLayerSnapshotRepository;
        this.marketFactRepository = marketFactRepository;
        this.reactionSnapshotRepository = reactionSnapshotRepository;
        this.regionRepository = regionRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional(readOnly = true)
    public RealEstateMapLayerResponse latestLayer(String layerType, String parentTargetId) {
        String normalizedLayerType = normalizeLayerType(layerType);
        RealEstateRegion parentRegion = resolveParentRegion(parentTargetId);
        String parentRegionCode = parentRegion == null ? null : parentRegion.getRegionCode();
        List<MapLayerSnapshotRow> rows = mapFeatureRepository.findLatestLayerRows(
                normalizedLayerType,
                parentRegionCode
        ).stream()
                .filter(RealEstateMapLayerService::isPriceMapLayerRow)
                .toList();
        Map<String, TargetAccumulator> targets = new LinkedHashMap<>();

        for (MapLayerSnapshotRow row : rows) {
            targets.computeIfAbsent(row.targetId(), TargetAccumulator::new).add(row);
        }

        List<RealEstateMapLayerTargetResponse> targetResponses = targets.values().stream()
                .map(TargetAccumulator::toResponse)
                .sorted(Comparator.comparing(RealEstateMapLayerTargetResponse::regionCode))
                .toList();
        String asOf = rows.stream()
                .map(MapLayerSnapshotRow::asOf)
                .max(Comparator.naturalOrder())
                .map(Instant::toString)
                .orElse(null);
        String sourceLabel = rows.stream()
                .map(MapLayerSnapshotRow::sourceLabel)
                .filter(value -> value != null && !value.isBlank())
                .findFirst()
                .orElse("map_layer_snapshots");
        String mapDataSource = rows.stream()
                .map(MapLayerSnapshotRow::assetSourceLabel)
                .filter(value -> value != null && !value.isBlank())
                .findFirst()
                .orElse("map_boundary_assets");
        String dataStatus = layerDataStatus(rows, targetResponses.isEmpty());
        boolean stale = rows.stream().anyMatch(MapLayerSnapshotRow::stale);

        return new RealEstateMapLayerResponse(
                normalizedLayerType,
                parentTargetId,
                parentRegionCode,
                asOf,
                sourceLabel,
                mapDataSource,
                dataStatus,
                stale,
                PERIOD_ORDER,
                targetResponses
        );
    }

    @Transactional
    public RealEstateMapLayerRefreshResponse refreshSnapshots(RealEstateMapLayerRefreshRequest request) {
        String layerType = normalizeLayerType(request.layerType());
        List<String> periods = normalizePeriods(request.periods());
        Instant asOf = request.asOf();
        Instant now = Instant.now();
        List<MapFeature> features = mapFeatureRepository.findByLayerTypeOrderByRegionCodeAsc(layerType);
        int accepted = 0;
        int skipped = 0;

        for (MapFeature feature : features) {
            for (String period : periods) {
                Optional<MapLayerComputation> computation = computeSnapshot(feature, period, asOf);
                if (computation.isEmpty()) {
                    skipped++;
                    continue;
                }
                MapLayerComputation value = computation.get();
                String id = mapRefreshId(layerType, feature.getTargetId(), period, value.asOf());
                MapLayerSnapshot snapshot = mapLayerSnapshotRepository
                        .findByTargetIdAndLayerTypeAndPeriodKeyAndAsOf(
                                feature.getTargetId(),
                                layerType,
                                period,
                                value.asOf()
                        )
                        .or(() -> mapLayerSnapshotRepository.findById(id))
                        .orElseGet(() -> new MapLayerSnapshot(id));
                snapshot.update(
                        feature.getTargetId(),
                        layerType,
                        period,
                        value.changePct(),
                        value.sampleCount(),
                        value.confidence(),
                        value.asOf(),
                        value.provider(),
                        value.sourceLabel(),
                        value.dataStatus(),
                        value.stale(),
                        now
                );
                mapLayerSnapshotRepository.save(snapshot);
                accepted++;
            }
        }

        return new RealEstateMapLayerRefreshResponse(
                layerType,
                periods,
                asOf.toString(),
                accepted,
                skipped
        );
    }

    private Optional<MapLayerComputation> computeSnapshot(MapFeature feature, String period, Instant asOf) {
        Optional<MapLayerComputation> officialPriceIndex = computeOfficialPriceIndexSnapshot(feature, period, asOf);
        if (officialPriceIndex.isPresent()) {
            return officialPriceIndex;
        }
        boolean priceIndexPeriod = officialPriceIndexWindowWeeks(period).isPresent()
                || officialPriceIndexWindowMonths(period).isPresent();

        LocalDate endDate = LocalDate.ofInstant(asOf, ZoneOffset.UTC);
        LocalDate startDate = endDate.minusDays(periodDays(period));
        List<RealEstateMarketFact> facts = findMapLayerOkFacts(feature, startDate, endDate);
        boolean staleWindow = false;
        if (facts.size() < 2) {
            Optional<LocalDate> fallbackEndDate = marketFactRepository.findLatestMapLayerObservedAt(
                    feature.getTargetId(),
                    "apt_trade",
                    endDate
            );
            if (fallbackEndDate.isEmpty()) {
                if (priceIndexPeriod) {
                    return Optional.empty();
                }
                return computeReactionOnlySnapshot(feature, asOf);
            }
            endDate = fallbackEndDate.get();
            startDate = endDate.minusDays(periodDays(period));
            facts = findMapLayerOkFacts(feature, startDate, endDate);
            staleWindow = true;
            if (facts.size() < 2) {
                if (priceIndexPeriod) {
                    return Optional.empty();
                }
                return computeReactionOnlySnapshot(feature, asOf);
            }
        }

        LocalDate firstObservedAt = facts.get(0).getObservedAt();
        LocalDate lastObservedAt = facts.get(facts.size() - 1).getObservedAt();
        if (firstObservedAt.equals(lastObservedAt)) {
            return Optional.empty();
        }

        BigDecimal firstAverage = averageDealAmount(facts, firstObservedAt);
        BigDecimal lastAverage = averageDealAmount(facts, lastObservedAt);
        if (firstAverage.signum() <= 0 || lastAverage.signum() <= 0) {
            return Optional.empty();
        }

        BigDecimal changePct = lastAverage.subtract(firstAverage)
                .multiply(BigDecimal.valueOf(100))
                .divide(firstAverage, 4, RoundingMode.HALF_UP);
        Optional<RealEstateReactionSnapshot> reactionSnapshot = latestReactionSnapshot(feature.getTargetId(), asOf);
        boolean extremeChange = changePct.abs().compareTo(EXTREME_CHANGE_THRESHOLD_PCT) > 0;
        BigDecimal sampleConfidence = sampleConfidence(facts.size());
        BigDecimal confidence = reactionSnapshot
                .map(snapshot -> BigDecimal.valueOf(snapshot.getConfidence()).setScale(4, RoundingMode.HALF_UP))
                .orElse(sampleConfidence);
        if (extremeChange) {
            confidence = confidence.min(sampleConfidence);
        }
        boolean stale = staleWindow
                || facts.stream().anyMatch(RealEstateMarketFact::isStale)
                || reactionSnapshot.map(RealEstateReactionSnapshot::isStale).orElse(false);
        boolean weak = stale || extremeChange;
        Instant snapshotAsOf = staleWindow ? lastObservedAt.atStartOfDay().toInstant(ZoneOffset.UTC) : asOf;

        return Optional.of(new MapLayerComputation(
                changePct,
                facts.size(),
                confidence,
                snapshotAsOf,
                weak ? "partial" : "ok",
                weak,
                MAP_REFRESH_PROVIDER,
                MAP_REFRESH_SOURCE_LABEL
        ));
    }

    private Optional<MapLayerComputation> computeOfficialPriceIndexSnapshot(
            MapFeature feature,
            String period,
            Instant asOf
    ) {
        Optional<MapLayerComputation> weeklySnapshot = computeWeeklyOfficialPriceIndexSnapshot(feature, period, asOf);
        if (weeklySnapshot.isPresent()) {
            return weeklySnapshot;
        }

        Optional<Integer> windowMonths = officialPriceIndexWindowMonths(period);
        if (windowMonths.isEmpty()) {
            return Optional.empty();
        }
        LocalDate endDate = LocalDate.ofInstant(asOf, ZoneOffset.UTC);
        List<String> lookupCodes = officialPriceIndexLookupCodes(feature, false);
        int requiredPoints = windowMonths.get() + 1;
        List<RealEstateMarketFact> facts = findLatestOfficialPriceIndexFacts(
                        feature,
                        lookupCodes,
                        OFFICIAL_PRICE_INDEX_FACT_TYPE,
                        OFFICIAL_PRICE_INDEX_MONTHLY_PROVIDER_DATASETS,
                        endDate,
                        PageRequest.of(0, Math.max(16, requiredPoints * OFFICIAL_PRICE_INDEX_MONTHLY_PROVIDER_DATASETS.size() * 3))
                ).stream()
                .filter(fact -> "ok".equals(fact.getDataStatus()))
                .collect(java.util.stream.Collectors.toMap(
                        RealEstateMarketFact::getObservedAt,
                        fact -> fact,
                        this::preferOfficialPriceIndexFact,
                        LinkedHashMap::new
                ))
                .values()
                .stream()
                .limit(requiredPoints)
                .toList();
        if (facts.size() < requiredPoints || !hasMonthlyWindow(facts, windowMonths.get())) {
            return Optional.empty();
        }

        return buildOfficialPriceIndexComputation(facts, windowMonths.get());
    }

    private Optional<MapLayerComputation> computeWeeklyOfficialPriceIndexSnapshot(
            MapFeature feature,
            String period,
            Instant asOf
    ) {
        Optional<Integer> windowWeeks = officialPriceIndexWindowWeeks(period);
        if (windowWeeks.isEmpty()) {
            return Optional.empty();
        }
        LocalDate endDate = LocalDate.ofInstant(asOf, ZoneOffset.UTC);
        List<String> lookupCodes = officialPriceIndexLookupCodes(feature, true);
        int requiredPoints = windowWeeks.get() + 1;
        List<RealEstateMarketFact> facts = findLatestOfficialPriceIndexFacts(
                        feature,
                        lookupCodes,
                        OFFICIAL_PRICE_INDEX_FACT_TYPE,
                        OFFICIAL_PRICE_INDEX_WEEKLY_PROVIDER_DATASETS,
                        endDate,
                        PageRequest.of(0, Math.max(8, requiredPoints * 3))
                ).stream()
                .filter(fact -> "ok".equals(fact.getDataStatus()))
                .collect(java.util.stream.Collectors.toMap(
                        RealEstateMarketFact::getObservedAt,
                        fact -> fact,
                        this::preferOfficialPriceIndexFact,
                        LinkedHashMap::new
                ))
                .values()
                .stream()
                .limit(requiredPoints)
                .toList();
        if (facts.size() < requiredPoints || !hasWeeklyWindow(facts, windowWeeks.get())) {
            return Optional.empty();
        }

        return buildOfficialPriceIndexComputation(facts, windowWeeks.get());
    }

    private List<RealEstateMarketFact> findLatestOfficialPriceIndexFacts(
            MapFeature feature,
            List<String> lookupCodes,
            String factType,
            List<String> providerDatasets,
            LocalDate endDate,
            PageRequest pageRequest
    ) {
        Map<String, RealEstateMarketFact> facts = new LinkedHashMap<>();
        String targetId = trimToNull(feature.getTargetId());
        if (targetId != null) {
            marketFactRepository.findLatestOfficialMapLayerFactsByTargetId(
                    targetId,
                    factType,
                    providerDatasets,
                    endDate,
                    pageRequest
            ).forEach(fact -> facts.putIfAbsent(officialFactLookupKey(fact), fact));
        }

        List<String> usableLookupCodes = lookupCodes.stream()
                .filter(code -> !"__none__".equals(code))
                .toList();
        if (!usableLookupCodes.isEmpty()) {
            marketFactRepository.findLatestOfficialMapLayerFactsByLegalDongCodeIn(
                    usableLookupCodes,
                    factType,
                    providerDatasets,
                    endDate,
                    pageRequest
            ).forEach(fact -> facts.putIfAbsent(officialFactLookupKey(fact), fact));
        }

        return facts.values().stream()
                .sorted(Comparator.comparing(RealEstateMarketFact::getObservedAt)
                        .reversed()
                        .thenComparing(RealEstateMarketFact::getProviderObjectId))
                .toList();
    }

    private Optional<MapLayerComputation> buildOfficialPriceIndexComputation(
            List<RealEstateMarketFact> facts,
            int windowSize
    ) {
        RealEstateMarketFact latestFact = facts.get(0);
        RealEstateMarketFact baselineFact = facts.get(windowSize);
        Optional<BigDecimal> latestIndex = marketFactDecimalValue(latestFact, "indexValue")
                .or(() -> marketFactDecimalValue(latestFact, "value"));
        Optional<BigDecimal> baselineIndex = marketFactDecimalValue(baselineFact, "indexValue")
                .or(() -> marketFactDecimalValue(baselineFact, "value"));
        if (latestIndex.isEmpty() || baselineIndex.isEmpty() || baselineIndex.get().signum() <= 0) {
            return Optional.empty();
        }

        BigDecimal confidence = facts.stream()
                .map(this::marketFactConfidence)
                .min(Comparator.naturalOrder())
                .orElse(BigDecimal.ONE.setScale(4, RoundingMode.HALF_UP));
        boolean stale = facts.stream().anyMatch(RealEstateMarketFact::isStale);
        int sampleCount = facts.stream()
                .mapToInt(this::marketFactSampleCount)
                .sum();

        BigDecimal changePct = latestIndex.get()
                .subtract(baselineIndex.get())
                .multiply(BigDecimal.valueOf(100))
                .divide(baselineIndex.get(), 4, RoundingMode.HALF_UP)
                .setScale(4, RoundingMode.HALF_UP);

        return Optional.of(new MapLayerComputation(
                changePct,
                sampleCount,
                confidence,
                latestFact.getAsOf().atStartOfDay().toInstant(ZoneOffset.UTC),
                stale ? "partial" : "ok",
                stale,
                latestFact.getProvider(),
                marketFactSourceLabel(latestFact)
        ));
    }

    private List<String> officialPriceIndexLookupCodes(MapFeature feature, boolean includeWeeklyFallbacks) {
        List<String> lookupCodes = new ArrayList<>();
        regionRepository.findById(feature.getTargetId()).ifPresent(region -> {
            String legalDongCode = region.getLegalDongCode();
            String regionCode = trimToNull(region.getRegionCode());
            addLookupCode(lookupCodes, legalDongCode);
            addLookupCode(
                    lookupCodes,
                    RONE_MONTHLY_SINGLE_TIER_LEGAL_DONG_CODES_BY_REGION_CODE.get(regionCode)
            );
            if (includeWeeklyFallbacks) {
                addWeeklyOfficialPriceIndexFallbackCodes(lookupCodes, legalDongCode);
                addLookupCode(
                        lookupCodes,
                        RONE_WEEKLY_SIDO_LEGAL_DONG_CODES_BY_REGION_CODE.get(regionCode)
                );
                addLookupCode(
                        lookupCodes,
                        RONE_WEEKLY_SINGLE_TIER_LEGAL_DONG_CODES_BY_REGION_CODE.get(regionCode)
                );
            }
        });
        if (lookupCodes.isEmpty()) {
            lookupCodes.add("__none__");
        }
        return lookupCodes;
    }

    private static void addWeeklyOfficialPriceIndexFallbackCodes(List<String> lookupCodes, String legalDongCode) {
        String parentSigunguCode = parentSigunguLegalDongCode(legalDongCode);
        addLookupCode(lookupCodes, parentSigunguCode);
        addLookupCode(lookupCodes, legacyGangwonLegalDongCode(legalDongCode));
        addLookupCode(lookupCodes, legacyGangwonLegalDongCode(parentSigunguCode));
        addLookupCode(lookupCodes, legacyJeonbukLegalDongCode(legalDongCode));
        addLookupCode(lookupCodes, legacyJeonbukLegalDongCode(parentSigunguCode));
    }

    private static String parentSigunguLegalDongCode(String value) {
        String trimmed = trimToNull(value);
        if (trimmed != null && trimmed.length() == 5 && !trimmed.endsWith("0")) {
            return trimmed.substring(0, 4) + "0";
        }
        return null;
    }

    private static String legacyGangwonLegalDongCode(String value) {
        String trimmed = trimToNull(value);
        if (trimmed != null && trimmed.startsWith("51") && trimmed.length() >= 5) {
            return "42" + trimmed.substring(2);
        }
        return null;
    }

    private static String legacyJeonbukLegalDongCode(String value) {
        String trimmed = trimToNull(value);
        if (trimmed != null && trimmed.startsWith("52") && trimmed.length() >= 5) {
            return "45" + trimmed.substring(2);
        }
        return null;
    }

    private static void addLookupCode(List<String> lookupCodes, String value) {
        String trimmed = trimToNull(value);
        if (trimmed != null && !lookupCodes.contains(trimmed)) {
            lookupCodes.add(trimmed);
        }
    }

    private static Optional<Integer> officialPriceIndexWindowMonths(String period) {
        return switch (period) {
            case "month" -> Optional.of(1);
            case "quarter" -> Optional.of(3);
            case "halfYear" -> Optional.of(6);
            case "year" -> Optional.of(12);
            default -> Optional.empty();
        };
    }

    private static Optional<Integer> officialPriceIndexWindowWeeks(String period) {
        return switch (period) {
            case "week" -> Optional.of(1);
            default -> Optional.empty();
        };
    }

    private RealEstateMarketFact preferOfficialPriceIndexFact(
            RealEstateMarketFact current,
            RealEstateMarketFact candidate
    ) {
        int currentPriority = officialPriceIndexDatasetPriority(current.getProviderDataset());
        int candidatePriority = officialPriceIndexDatasetPriority(candidate.getProviderDataset());
        if (candidatePriority != currentPriority) {
            return candidatePriority < currentPriority ? candidate : current;
        }
        return candidate.getIngestedAt().isAfter(current.getIngestedAt()) ? candidate : current;
    }

    private static String officialFactLookupKey(RealEstateMarketFact fact) {
        return "%s|%s|%s".formatted(
                fact.getProvider(),
                fact.getProviderDataset(),
                fact.getProviderObjectId()
        );
    }

    private static int officialPriceIndexDatasetPriority(String providerDataset) {
        if (OFFICIAL_PRICE_INDEX_WEEKLY_DATASET.equals(providerDataset)) {
            return 0;
        }
        if (OFFICIAL_PRICE_INDEX_MONTHLY_DATASET.equals(providerDataset)) {
            return 0;
        }
        return 9;
    }

    private static boolean hasMonthlyWindow(List<RealEstateMarketFact> facts, int windowMonths) {
        if (facts.isEmpty() || facts.size() <= windowMonths) {
            return false;
        }
        YearMonth latestMonth = YearMonth.from(facts.get(0).getObservedAt());
        YearMonth baselineMonth = YearMonth.from(facts.get(windowMonths).getObservedAt());
        return baselineMonth.plusMonths(windowMonths).equals(latestMonth);
    }

    private static boolean hasWeeklyWindow(List<RealEstateMarketFact> facts, int windowWeeks) {
        if (facts.isEmpty() || facts.size() <= windowWeeks) {
            return false;
        }
        LocalDate latestDate = facts.get(0).getObservedAt();
        LocalDate baselineDate = facts.get(windowWeeks).getObservedAt();
        return ChronoUnit.WEEKS.between(baselineDate, latestDate) == windowWeeks;
    }

    private List<RealEstateMarketFact> findMapLayerOkFacts(
            MapFeature feature,
            LocalDate startDate,
            LocalDate endDate
    ) {
        return marketFactRepository.findMapLayerFacts(
                        feature.getTargetId(),
                        "apt_trade",
                        startDate,
                        endDate
                ).stream()
                .filter(fact -> "ok".equals(fact.getDataStatus()))
                .toList();
    }

    private Optional<RealEstateReactionSnapshot> latestReactionSnapshot(String targetId, Instant asOf) {
        return reactionSnapshotRepository.findLatestForMapLayer(
                targetId,
                asOf,
                PageRequest.of(0, 1)
        ).stream().findFirst();
    }

    private Optional<MapLayerComputation> computeReactionOnlySnapshot(MapFeature feature, Instant asOf) {
        return latestReactionSnapshot(feature.getTargetId(), asOf)
                .map(snapshot -> new MapLayerComputation(
                        reactionChangePct(snapshot),
                        snapshot.getMentionCount(),
                        BigDecimal.valueOf(snapshot.getConfidence()).setScale(4, RoundingMode.HALF_UP),
                        snapshot.getAsOf(),
                        "partial",
                        snapshot.isStale(),
                        REACTION_ONLY_PROVIDER,
                        REACTION_ONLY_SOURCE_LABEL
                ));
    }

    private static BigDecimal reactionChangePct(RealEstateReactionSnapshot snapshot) {
        double directionScore = snapshot.getExpectationScore() - snapshot.getConcernScore();
        double deltaScore = mentionDeltaPct(snapshot) / 100.0;
        double signedScore = directionScore == 0
                ? deltaScore
                : directionScore * 0.7 + deltaScore * 0.3;
        double capped = Math.max(-0.65, Math.min(0.65, signedScore));
        return BigDecimal.valueOf(capped).setScale(4, RoundingMode.HALF_UP);
    }

    private static double mentionDeltaPct(RealEstateReactionSnapshot snapshot) {
        int previous = snapshot.getPreviousMentionCount();
        if (previous <= 0) {
            return snapshot.getMentionCount() > 0 ? 100 : 0;
        }
        return ((double) snapshot.getMentionCount() - previous) * 100.0 / previous;
    }

    private BigDecimal averageDealAmount(List<RealEstateMarketFact> facts, LocalDate observedAt) {
        List<BigDecimal> values = new ArrayList<>();
        for (RealEstateMarketFact fact : facts) {
            if (!observedAt.equals(fact.getObservedAt())) {
                continue;
            }
            dealAmount(fact).ifPresent(values::add);
        }
        if (values.isEmpty()) {
            return BigDecimal.ZERO;
        }
        BigDecimal sum = values.stream().reduce(BigDecimal.ZERO, BigDecimal::add);
        return sum.divide(BigDecimal.valueOf(values.size()), 4, RoundingMode.HALF_UP);
    }

    private Optional<BigDecimal> dealAmount(RealEstateMarketFact fact) {
        try {
            JsonNode root = objectMapper.readTree(fact.getValueJson());
            JsonNode value = root.path("dealAmountManwon");
            if (value.isNumber()) {
                return Optional.of(BigDecimal.valueOf(value.asDouble()));
            }
            if (value.isTextual()) {
                return parseDecimal(value.asText());
            }
            JsonNode rawDealAmount = root.path("dealAmount");
            if (rawDealAmount.isTextual()) {
                return parseDecimal(rawDealAmount.asText());
            }
            return Optional.empty();
        } catch (JsonProcessingException exc) {
            return Optional.empty();
        }
    }

    private Optional<BigDecimal> marketFactDecimalValue(RealEstateMarketFact fact, String fieldName) {
        try {
            JsonNode root = objectMapper.readTree(fact.getValueJson());
            JsonNode value = root.path(fieldName);
            if (value.isNumber()) {
                return Optional.of(BigDecimal.valueOf(value.asDouble()));
            }
            if (value.isTextual()) {
                return parseDecimal(value.asText());
            }
            return Optional.empty();
        } catch (JsonProcessingException exc) {
            return Optional.empty();
        }
    }

    private int marketFactSampleCount(RealEstateMarketFact fact) {
        try {
            JsonNode root = objectMapper.readTree(fact.getValueJson());
            JsonNode sampleCount = root.path("sampleCount");
            if (sampleCount.isInt() && sampleCount.asInt() > 0) {
                return sampleCount.asInt();
            }
        } catch (JsonProcessingException ignored) {
            // Fall through to the official statistic default.
        }
        return 1;
    }

    private BigDecimal marketFactConfidence(RealEstateMarketFact fact) {
        try {
            JsonNode root = objectMapper.readTree(fact.getValueJson());
            JsonNode confidence = root.path("confidence");
            if (confidence.isNumber()) {
                return BigDecimal.valueOf(confidence.asDouble()).setScale(4, RoundingMode.HALF_UP);
            }
            if (confidence.isTextual()) {
                return parseDecimal(confidence.asText())
                        .map(value -> value.setScale(4, RoundingMode.HALF_UP))
                        .orElse(BigDecimal.ONE.setScale(4, RoundingMode.HALF_UP));
            }
        } catch (JsonProcessingException ignored) {
            // Fall through to the official statistic default.
        }
        return BigDecimal.ONE.setScale(4, RoundingMode.HALF_UP);
    }

    private String marketFactSourceLabel(RealEstateMarketFact fact) {
        try {
            JsonNode root = objectMapper.readTree(fact.getValueJson());
            JsonNode sourceLabel = root.path("sourceLabel");
            if (sourceLabel.isTextual() && !sourceLabel.asText().isBlank()) {
                return sourceLabel.asText();
            }
        } catch (JsonProcessingException ignored) {
            // Fall through to the official source label default.
        }
        return OFFICIAL_PRICE_INDEX_SOURCE_LABEL;
    }

    private Optional<BigDecimal> parseDecimal(String value) {
        String normalized = value == null ? "" : value.replace(",", "").trim();
        if (normalized.isBlank()) {
            return Optional.empty();
        }
        try {
            return Optional.of(new BigDecimal(normalized));
        } catch (NumberFormatException exc) {
            return Optional.empty();
        }
    }

    private static BigDecimal sampleConfidence(int sampleCount) {
        double confidence = Math.min(1.0, Math.max(0.1, sampleCount / 50.0));
        return BigDecimal.valueOf(confidence).setScale(4, RoundingMode.HALF_UP);
    }

    private static long periodDays(String period) {
        return switch (period) {
            case "week" -> 7L;
            case "month" -> 31L;
            case "quarter" -> 92L;
            case "halfYear" -> 183L;
            case "year" -> 366L;
            default -> throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Unsupported map period: " + period
            );
        };
    }

    private static List<String> normalizePeriods(List<String> values) {
        return values.stream()
                .map(RealEstateMapLayerService::normalizePeriod)
                .distinct()
                .toList();
    }

    private static String normalizePeriod(String value) {
        String trimmed = trimToNull(value);
        if (trimmed == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Map period is required");
        }
        String normalized = trimmed.toLowerCase(Locale.ROOT);
        if ("1week".equals(normalized)
                || "1weeks".equals(normalized)
                || "oneweek".equals(normalized)
                || "oneweeks".equals(normalized)) {
            return "week";
        }
        if ("1month".equals(normalized)
                || "1months".equals(normalized)
                || "onemonth".equals(normalized)
                || "onemonths".equals(normalized)) {
            return "month";
        }
        if ("halfyear".equals(normalized)
                || "6month".equals(normalized)
                || "6months".equals(normalized)) {
            return "halfYear";
        }
        if ("3month".equals(normalized)
                || "3months".equals(normalized)
                || "threemonth".equals(normalized)
                || "threemonths".equals(normalized)) {
            return "quarter";
        }
        if ("12month".equals(normalized)
                || "12months".equals(normalized)
                || "1year".equals(normalized)
                || "1years".equals(normalized)
                || "oneyear".equals(normalized)
                || "oneyears".equals(normalized)) {
            return "year";
        }
        if (!PERIOD_ORDER.contains(trimmed)) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Unsupported map period: " + trimmed
            );
        }
        return trimmed;
    }

    private static String mapRefreshId(String layerType, String targetId, String period, Instant asOf) {
        return "map-refresh-%s-%s-%s-%s".formatted(
                layerType,
                targetId,
                period,
                DateTimeFormatter.ofPattern("yyyyMMddHHmmss")
                        .withZone(ZoneOffset.UTC)
                        .format(asOf)
        );
    }

    private RealEstateRegion resolveParentRegion(String parentTargetId) {
        String trimmed = trimToNull(parentTargetId);
        if (trimmed == null) {
            return null;
        }
        return regionRepository.findById(trimmed)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "Unknown parentTargetId: " + trimmed
                ));
    }

    private static String normalizeLayerType(String value) {
        String trimmed = trimToNull(value);
        if (trimmed == null) {
            return "sido";
        }
        String normalized = trimmed.toLowerCase(Locale.ROOT);
        if (!List.of("sido", "sigungu", "eupmyeondong").contains(normalized)) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Unsupported map layerType: " + trimmed
            );
        }
        return normalized;
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static double decimalToDouble(BigDecimal value) {
        return value == null ? 0 : value.doubleValue();
    }

    private static double confidencePct(BigDecimal value) {
        if (value == null) {
            return 0;
        }
        double raw = value.doubleValue();
        return roundToSingleDecimal(raw <= 1 ? raw * 100 : raw);
    }

    private static double roundToSingleDecimal(double value) {
        return Math.round(value * 10.0) / 10.0;
    }

    private static boolean isPriceMapLayerRow(MapLayerSnapshotRow row) {
        String provider = row.provider() == null ? "" : row.provider().toLowerCase(Locale.ROOT);
        String dataStatus = row.dataStatus() == null ? "" : row.dataStatus().toLowerCase(Locale.ROOT);
        return !"real_estate_reaction_snapshots".equals(provider)
                && !"reaction_snapshots".equals(provider)
                && !"seed".equals(provider)
                && !"mock".equals(dataStatus);
    }

    private static String layerDataStatus(List<MapLayerSnapshotRow> rows, boolean empty) {
        if (empty) {
            return "empty";
        }
        if (rows.stream().allMatch(row -> "mock".equals(row.dataStatus()))) {
            return "mock";
        }
        if (rows.stream().allMatch(row -> "ok".equals(row.dataStatus()))) {
            return "ok";
        }
        return "partial";
    }

    private record MapLayerComputation(
            BigDecimal changePct,
            int sampleCount,
            BigDecimal confidence,
            Instant asOf,
            String dataStatus,
            boolean stale,
            String provider,
            String sourceLabel
    ) {
    }

    private static final class TargetAccumulator {
        private final String targetId;
        private String targetType;
        private String displayName;
        private String slug;
        private String regionLevel;
        private String regionCode;
        private String legalDongCode;
        private String parentTargetId;
        private String geometryId;
        private final Map<String, RealEstateMapLayerPeriodResponse> periods = new LinkedHashMap<>();

        private TargetAccumulator(String targetId) {
            this.targetId = targetId;
        }

        private void add(MapLayerSnapshotRow row) {
            this.targetType = row.targetType();
            this.displayName = row.displayName();
            this.slug = row.slug();
            this.regionLevel = row.regionLevel();
            this.regionCode = row.regionCode();
            this.legalDongCode = row.legalDongCode();
            this.parentTargetId = row.parentTargetId();
            this.geometryId = row.geometryId();
            this.periods.put(
                    row.periodKey(),
                    new RealEstateMapLayerPeriodResponse(
                            decimalToDouble(row.changePct()),
                            row.sampleCount(),
                            confidencePct(row.confidence()),
                            row.asOf().toString(),
                            row.provider(),
                            row.sourceLabel(),
                            row.dataStatus(),
                            row.stale()
                    )
            );
        }

        private RealEstateMapLayerTargetResponse toResponse() {
            Map<String, RealEstateMapLayerPeriodResponse> orderedPeriods = new LinkedHashMap<>();
            for (String period : PERIOD_ORDER) {
                if (periods.containsKey(period)) {
                    orderedPeriods.put(period, periods.get(period));
                }
            }
            return new RealEstateMapLayerTargetResponse(
                    targetId,
                    targetType,
                    displayName,
                    slug,
                    regionLevel,
                    regionCode,
                    legalDongCode,
                    parentTargetId,
                    geometryId,
                    orderedPeriods
            );
        }
    }
}
