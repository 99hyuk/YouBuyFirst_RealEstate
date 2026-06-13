package com.youbuyfirst.backend.realestate.dto;

public record RealEstateTargetEdgeResponse(
        Long edgeId,
        String fromTargetType,
        String fromTargetId,
        String fromDisplayName,
        String fromSlug,
        String toTargetType,
        String toTargetId,
        String toDisplayName,
        String toSlug,
        String edgeType,
        Double confidence,
        String source,
        String reviewState
) {
}
