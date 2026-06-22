package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateTargetEdgeBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetEdgeRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetEdgeResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Objects;

@Service
public class RealEstateTargetGraphService {

    private final RealEstateTargetRepository targetRepository;
    private final RealEstateTargetEdgeRepository edgeRepository;

    public RealEstateTargetGraphService(
            RealEstateTargetRepository targetRepository,
            RealEstateTargetEdgeRepository edgeRepository
    ) {
        this.targetRepository = targetRepository;
        this.edgeRepository = edgeRepository;
    }

    @Transactional
    public RealEstateTargetEdgeBatchResponse upsertEdges(Collection<RealEstateTargetEdgeRequest> requests) {
        List<RealEstateTargetEdgeRequest> items = requests == null
                ? List.of()
                : requests.stream().filter(Objects::nonNull).toList();
        Instant now = Instant.now();
        int accepted = 0;
        int created = 0;
        int updated = 0;
        int skipped = 0;

        for (RealEstateTargetEdgeRequest item : items) {
            String fromTargetId = requireText(item.fromTargetId(), "fromTargetId");
            String toTargetId = requireText(item.toTargetId(), "toTargetId");
            String edgeType = normalizeLower(requireText(item.edgeType(), "edgeType"));

            if (fromTargetId.equals(toTargetId)) {
                skipped++;
                continue;
            }

            RealEstateTarget fromTarget = targetRepository.findById(fromTargetId)
                    .orElseThrow(() -> new IllegalArgumentException("from target not found: " + fromTargetId));
            RealEstateTarget toTarget = targetRepository.findById(toTargetId)
                    .orElseThrow(() -> new IllegalArgumentException("to target not found: " + toTargetId));
            String fromTargetType = normalizeLower(requireText(item.fromTargetType(), "fromTargetType"));
            String toTargetType = normalizeLower(requireText(item.toTargetType(), "toTargetType"));
            ensureTargetTypeMatches(fromTarget, fromTargetType, "fromTargetType");
            ensureTargetTypeMatches(toTarget, toTargetType, "toTargetType");

            Double confidence = clampConfidence(item.confidence());
            String source = defaultIfBlank(item.source(), "import:unknown");
            String reviewState = normalizeLower(defaultIfBlank(item.reviewState(), "candidate"));

            boolean[] isCreated = {false};
            RealEstateTargetEdge edge = edgeRepository.findByFromTargetIdAndToTargetIdAndEdgeType(
                            fromTargetId,
                            toTargetId,
                            edgeType
                    )
                    .orElseGet(() -> {
                        isCreated[0] = true;
                        return new RealEstateTargetEdge(
                                fromTargetId,
                                fromTargetType,
                                toTargetId,
                                toTargetType,
                                edgeType,
                                confidence,
                                source,
                                reviewState,
                                now
                        );
                    });
            if (!isCreated[0]) {
                edge.update(
                        fromTargetType,
                        toTargetType,
                        edgeType,
                        confidence,
                        source,
                        reviewState,
                        now
                );
                updated++;
            } else {
                created++;
            }
            edgeRepository.save(edge);
            accepted++;
        }

        return new RealEstateTargetEdgeBatchResponse(accepted, created, updated, skipped);
    }

    @Transactional(readOnly = true)
    public List<RealEstateTargetEdgeResponse> publicGraph(
            String targetId,
            String direction,
            String edgeType,
            int limit
    ) {
        targetRepository.findById(targetId)
                .orElseThrow(() -> new IllegalArgumentException("real-estate target not found: " + targetId));
        return search(targetId, direction, edgeType, "approved", limit, 0);
    }

    @Transactional(readOnly = true)
    public List<RealEstateTargetEdgeResponse> internalEdges(
            String targetId,
            String direction,
            String edgeType,
            String reviewState,
            int limit,
            int page
    ) {
        return search(targetId, direction, edgeType, reviewState, limit, page);
    }

    private List<RealEstateTargetEdgeResponse> search(
            String targetId,
            String direction,
            String edgeType,
            String reviewState,
            int limit,
            int page
    ) {
        int boundedLimit = Math.max(1, Math.min(limit, 1000));
        int boundedPage = Math.max(0, page);
        return edgeRepository.searchEdges(
                        trimToNull(targetId),
                        normalizeDirection(direction),
                        normalizeNullable(edgeType),
                        normalizeNullable(reviewState),
                        PageRequest.of(boundedPage, boundedLimit)
                )
                .stream()
                .map(this::toResponse)
                .toList();
    }

    private RealEstateTargetEdgeResponse toResponse(RealEstateTargetEdge edge) {
        RealEstateTarget fromTarget = edge.getFromTarget();
        RealEstateTarget toTarget = edge.getToTarget();
        return new RealEstateTargetEdgeResponse(
                edge.getId(),
                edge.getFromTargetType(),
                edge.getFromTargetId(),
                fromTarget.getDisplayName(),
                fromTarget.getSlug(),
                edge.getToTargetType(),
                edge.getToTargetId(),
                toTarget.getDisplayName(),
                toTarget.getSlug(),
                edge.getEdgeType(),
                edge.getConfidence(),
                edge.getSource(),
                edge.getReviewState()
        );
    }

    private static void ensureTargetTypeMatches(RealEstateTarget target, String expectedType, String fieldName) {
        String actualType = normalizeLower(target.getTargetType());
        if (!actualType.equals(expectedType)) {
            throw new IllegalArgumentException(fieldName + " does not match target: " + target.getId());
        }
    }

    private static String requireText(String value, String fieldName) {
        String trimmed = trimToNull(value);
        if (trimmed == null) {
            throw new IllegalArgumentException(fieldName + " is required");
        }
        return trimmed;
    }

    private static String defaultIfBlank(String value, String fallback) {
        String trimmed = trimToNull(value);
        return trimmed == null ? fallback : trimmed;
    }

    private static String normalizeNullable(String value) {
        String trimmed = trimToNull(value);
        return trimmed == null ? null : normalizeLower(trimmed);
    }

    private static String normalizeLower(String value) {
        return value.trim().toLowerCase(Locale.ROOT);
    }

    private static String normalizeDirection(String value) {
        String normalized = normalizeNullable(value);
        if ("in".equals(normalized) || "out".equals(normalized) || "both".equals(normalized)) {
            return normalized;
        }
        return "both";
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static Double clampConfidence(Double value) {
        if (value == null) {
            return 0.5;
        }
        return Math.max(0.0, Math.min(1.0, value));
    }
}
