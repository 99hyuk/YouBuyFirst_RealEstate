package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateNearbyComplexListResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateNearbyComplexResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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

    @Transactional(readOnly = true)
    public RealEstateNearbyComplexListResponse nearbyComplexes(String targetId, int limit) {
        String normalizedTargetId = requireText(targetId, "targetId");
        targetRepository.findById(normalizedTargetId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "unknown real-estate target: " + normalizedTargetId
                ));

        int boundedLimit = Math.max(1, Math.min(limit, 100));
        List<RealEstateComplex> complexes = complexRepository.findVisibleMarkersForTarget(
                normalizedTargetId,
                PageRequest.of(0, boundedLimit)
        );
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
        String provider = defaultIfBlank(complex.getCoordinateProvider(), "unknown");
        boolean stale = complex.isMarkerStale() || isWeakStatus(dataStatus) || isWeakStatus(complex.getCoordinateStatus());

        return new RealEstateNearbyComplexResponse(
                complex.getTargetId(),
                name,
                defaultIfBlank(complex.getRoadAddress(), complex.getJibunAddress()),
                defaultIfBlank(regionName, complex.getRegionTargetId()),
                decimalToDouble(complex.getLatitude()),
                decimalToDouble(complex.getLongitude()),
                defaultIfBlank(complex.getMarkerTone(), "flat"),
                defaultIfBlank(complex.getPriceSummary(), "확인 필요"),
                defaultIfBlank(complex.getChangeLabel(), "unknown"),
                defaultIfBlank(complex.getReactionSummary(), "반응 지표 연결 전"),
                provider,
                instantToString(complex.getCoordinateAsOf()),
                dataStatus,
                stale,
                defaultIfBlank(complex.getMarkerNote(), "좌표와 시장 fact 검증이 필요한 marker입니다."),
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

    private static String requireText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, fieldName + " is required");
        }
        return value.trim();
    }
}
