package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerPeriodResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerTargetResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
public class RealEstateMapLayerService {

    private static final List<String> PERIOD_ORDER = List.of("week", "month", "halfYear");

    private final MapFeatureRepository mapFeatureRepository;
    private final RealEstateRegionRepository regionRepository;

    public RealEstateMapLayerService(
            MapFeatureRepository mapFeatureRepository,
            RealEstateRegionRepository regionRepository
    ) {
        this.mapFeatureRepository = mapFeatureRepository;
        this.regionRepository = regionRepository;
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
        String dataStatus = targetResponses.isEmpty()
                ? "empty"
                : rows.stream().allMatch(row -> "mock".equals(row.dataStatus())) ? "mock" : "ok";
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
