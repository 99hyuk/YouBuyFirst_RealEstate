package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateComplexBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateComplexRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateNearbyComplexListResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateNearbyComplexResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Locale;

@Service
public class RealEstateComplexService {

    private final RealEstateComplexRepository complexRepository;
    private final RealEstateTargetRepository targetRepository;

    public RealEstateComplexService(
            RealEstateComplexRepository complexRepository,
            RealEstateTargetRepository targetRepository
    ) {
        this.complexRepository = complexRepository;
        this.targetRepository = targetRepository;
    }

    @Transactional
    public RealEstateComplexBatchResponse upsertComplexes(Collection<RealEstateComplexRequest> requests) {
        List<RealEstateComplexRequest> items = requests == null
                ? List.of()
                : requests.stream().filter(Objects::nonNull).toList();
        Instant now = Instant.now();
        int accepted = 0;
        int created = 0;
        int updated = 0;
        int skipped = 0;

        for (RealEstateComplexRequest item : items) {
            String targetId = requireText(item.targetId(), "targetId");
            RealEstateTarget target = targetRepository.findById(targetId)
                    .orElseThrow(() -> new ResponseStatusException(
                            HttpStatus.BAD_REQUEST,
                            "unknown real-estate complex target: " + targetId
                    ));
            if (!"complex".equalsIgnoreCase(target.getTargetType())) {
                skipped++;
                continue;
            }
            String regionTargetId = trimToNull(item.regionTargetId());
            if (regionTargetId != null) {
                targetRepository.findById(regionTargetId)
                        .orElseThrow(() -> new ResponseStatusException(
                                HttpStatus.BAD_REQUEST,
                                "unknown real-estate region target: " + regionTargetId
                        ));
            }

            boolean[] isCreated = {false};
            RealEstateComplex complex = complexRepository.findById(targetId)
                    .orElseGet(() -> {
                        isCreated[0] = true;
                        return new RealEstateComplex(
                                targetId,
                                regionTargetId,
                                trimToNull(item.legalDongCode()),
                                trimToNull(item.roadAddress()),
                                trimToNull(item.jibunAddress()),
                                trimToNull(item.normalizedAddress()),
                                item.builtYear(),
                                item.householdCount(),
                                defaultIfBlank(item.source(), "import:unknown"),
                                now
                        );
                    });
            complex.update(
                    regionTargetId,
                    trimToNull(item.legalDongCode()),
                    trimToNull(item.roadAddress()),
                    trimToNull(item.jibunAddress()),
                    trimToNull(item.normalizedAddress()),
                    item.builtYear(),
                    item.householdCount(),
                    defaultIfBlank(item.source(), "import:unknown"),
                    item.latitude(),
                    item.longitude(),
                    trimToNull(item.coordinateProvider()),
                    parseInstantOrNull(item.coordinateAsOf()),
                    trimToNull(item.coordinateStatus()),
                    trimToNull(item.markerTone()),
                    trimToNull(item.priceSummary()),
                    trimToNull(item.changeLabel()),
                    trimToNull(item.reactionSummary()),
                    trimToNull(item.markerNote()),
                    defaultIfBlank(item.markerDataStatus(), "unknown"),
                    item.markerStale(),
                    now
            );
            complexRepository.save(complex);
            accepted++;
            if (isCreated[0]) {
                created++;
            } else {
                updated++;
            }
        }

        return new RealEstateComplexBatchResponse(accepted, created, updated, skipped);
    }

    @Transactional(readOnly = true)
    public RealEstateNearbyComplexListResponse nearbyComplexes(String targetId, int limit) {
        String normalizedTargetId = requireText(targetId, "targetId");
        RealEstateTarget requestedTarget = targetRepository.findById(normalizedTargetId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "unknown real-estate target: " + normalizedTargetId
                ));

        int boundedLimit = Math.max(1, Math.min(limit, 100));
        List<RealEstateComplex> complexes = complexRepository.findVisibleMarkersForTarget(
                normalizedTargetId,
                PageRequest.of(0, boundedLimit)
        );
        if (needsCanonicalMarkerFallback(requestedTarget, complexes)) {
            complexes = mergeCanonicalFallbackMarkers(
                    normalizedTargetId,
                    requestedTarget,
                    complexes,
                    boundedLimit
            );
        }
        Map<String, String> regionNames = regionNames(complexes);
        List<RealEstateNearbyComplexResponse> items = complexes.stream()
                .map(complex -> toResponse(complex, regionNames.get(complex.getRegionTargetId())))
                .toList();
        String dataStatus = resolveDataStatus(items);
        boolean stale = items.isEmpty() || items.stream().anyMatch(RealEstateNearbyComplexResponse::stale);

        return new RealEstateNearbyComplexListResponse(
                normalizedTargetId,
                dataStatus,
                stale,
                items
        );
    }

    private List<RealEstateComplex> mergeCanonicalFallbackMarkers(
            String targetId,
            RealEstateTarget requestedTarget,
            List<RealEstateComplex> directMarkers,
            int limit
    ) {
        String rawQuery = trimToNull(requestedTarget.getDisplayName());
        if (rawQuery == null) {
            return directMarkers;
        }
        String lowerQuery = rawQuery.toLowerCase(Locale.ROOT);
        String normalizedNameQuery = lowerQuery.replace(" ", "");
        String aliasQuery = RealEstateAlias.normalizeAlias(rawQuery);
        if (aliasQuery.isBlank() && normalizedNameQuery.isBlank()) {
            return directMarkers;
        }

        List<RealEstateComplex> canonicalMarkers = complexRepository.findCanonicalMarkersByNameOrAlias(
                targetId,
                lowerQuery,
                normalizedNameQuery,
                aliasQuery,
                PageRequest.of(0, limit)
        );
        if (canonicalMarkers.isEmpty()) {
            return directMarkers;
        }

        LinkedHashMap<String, RealEstateComplex> merged = new LinkedHashMap<>();
        for (RealEstateComplex marker : canonicalMarkers) {
            merged.put(marker.getTargetId(), marker);
        }
        for (RealEstateComplex marker : directMarkers) {
            if (merged.size() >= limit) {
                break;
            }
            merged.putIfAbsent(marker.getTargetId(), marker);
        }
        return new ArrayList<>(merged.values());
    }

    private static boolean needsCanonicalMarkerFallback(
            RealEstateTarget requestedTarget,
            List<RealEstateComplex> complexes
    ) {
        if (!"complex".equalsIgnoreCase(requestedTarget.getTargetType())) {
            return false;
        }
        if (complexes.isEmpty()) {
            return true;
        }
        return complexes.stream().noneMatch(RealEstateComplexService::hasUsableMarker);
    }

    private static boolean hasUsableMarker(RealEstateComplex complex) {
        return complex.getLatitude() != null
                && complex.getLongitude() != null
                && !isWeakStatus(complex.getMarkerDataStatus())
                && !isWeakStatus(complex.getCoordinateStatus());
    }

    private Map<String, String> regionNames(List<RealEstateComplex> complexes) {
        Map<String, String> names = new HashMap<>();
        complexes.stream()
                .map(RealEstateComplex::getRegionTargetId)
                .filter(value -> value != null && !value.isBlank())
                .distinct()
                .forEach(regionTargetId -> targetRepository.findById(regionTargetId)
                        .ifPresent(region -> names.put(regionTargetId, region.getDisplayName())));
        return names;
    }

    private static RealEstateNearbyComplexResponse toResponse(RealEstateComplex complex, String regionName) {
        RealEstateTarget target = complex.getTarget();
        String name = target == null ? complex.getTargetId() : target.getDisplayName();
        String dataStatus = defaultIfBlank(complex.getMarkerDataStatus(), complex.getCoordinateStatus());
        String provider = defaultIfBlank(complex.getCoordinateProvider(), defaultIfBlank(complex.getSource(), "unknown"));
        boolean stale = complex.isMarkerStale() || isWeakStatus(dataStatus) || isWeakStatus(complex.getCoordinateStatus());

        return new RealEstateNearbyComplexResponse(
                complex.getTargetId(),
                name,
                defaultIfBlank(complex.getRoadAddress(), complex.getJibunAddress()),
                defaultIfBlank(regionName, complex.getRegionTargetId()),
                decimalToDouble(complex.getLatitude()),
                decimalToDouble(complex.getLongitude()),
                defaultIfBlank(complex.getMarkerTone(), "flat"),
                defaultIfBlank(complex.getPriceSummary(), "\uD655\uC778 \uD544\uC694"),
                defaultIfBlank(complex.getChangeLabel(), "unknown"),
                defaultIfBlank(complex.getReactionSummary(), "\uBC18\uC751 \uC9C0\uD45C \uC5F0\uACB0 \uC804"),
                provider,
                instantToString(complex.getCoordinateAsOf()),
                dataStatus,
                stale,
                defaultIfBlank(complex.getMarkerNote(), "\uC88C\uD45C\uC640 \uC2DC\uC7A5 fact \uAC80\uC99D\uC774 \uD544\uC694\uD55C marker\uC785\uB2C8\uB2E4."),
                complex.getLegalDongCode(),
                provider,
                defaultIfBlank(complex.getCoordinateStatus(), "unknown")
        );
    }

    private static String resolveDataStatus(List<RealEstateNearbyComplexResponse> items) {
        if (items.isEmpty()) {
            return "empty";
        }
        boolean allMock = items.stream().allMatch(item -> "mock".equals(item.dataStatus()));
        boolean anyWeak = items.stream().anyMatch(item -> isWeakStatus(item.dataStatus()));
        if (allMock) {
            return "mock";
        }
        return anyWeak ? "partial" : "ok";
    }

    private static Double decimalToDouble(BigDecimal value) {
        return value == null ? null : value.doubleValue();
    }

    private static String instantToString(Instant value) {
        return value == null ? null : value.toString();
    }

    private static boolean isWeakStatus(String value) {
        String normalized = value == null ? "" : value.trim().toLowerCase();
        return normalized.isBlank()
                || "mock".equals(normalized)
                || "candidate".equals(normalized)
                || "unknown".equals(normalized)
                || "stale".equals(normalized);
    }

    private static String defaultIfBlank(String value, String fallback) {
        if (value == null || value.isBlank()) {
            return fallback;
        }
        return value.trim();
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static Instant parseInstantOrNull(String value) {
        String normalized = trimToNull(value);
        if (normalized == null) {
            return null;
        }
        return Instant.parse(normalized);
    }

    private static String requireText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, fieldName + " is required");
        }
        return value.trim();
    }
}
