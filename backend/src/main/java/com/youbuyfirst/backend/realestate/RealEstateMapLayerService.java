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
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;

@Service
public class RealEstateMapLayerService {

    private static final List<String> PERIOD_ORDER = List.of("week", "month", "halfYear");
    private static final String MAP_REFRESH_PROVIDER = "real_estate_map_layer_refresh";
    private static final String MAP_REFRESH_SOURCE_LABEL = "실거래 market facts + 반응 snapshot";
    private static final BigDecimal EXTREME_CHANGE_THRESHOLD_PCT = BigDecimal.valueOf(50);

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
        );
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
                MapLayerSnapshot snapshot = mapLayerSnapshotRepository.findById(id)
                        .orElseGet(() -> new MapLayerSnapshot(id));
                snapshot.update(
                        feature.getTargetId(),
                        layerType,
                        period,
                        value.changePct(),
                        value.sampleCount(),
                        value.confidence(),
                        value.asOf(),
                        MAP_REFRESH_PROVIDER,
                        MAP_REFRESH_SOURCE_LABEL,
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
                return Optional.empty();
            }
            endDate = fallbackEndDate.get();
            startDate = endDate.minusDays(periodDays(period));
            facts = findMapLayerOkFacts(feature, startDate, endDate);
            staleWindow = true;
            if (facts.size() < 2) {
                return Optional.empty();
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
                weak
        ));
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
            case "halfYear" -> 183L;
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
        if ("halfyear".equals(trimmed.toLowerCase(Locale.ROOT))) {
            return "halfYear";
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
            boolean stale
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
            periods.forEach(orderedPeriods::putIfAbsent);
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
