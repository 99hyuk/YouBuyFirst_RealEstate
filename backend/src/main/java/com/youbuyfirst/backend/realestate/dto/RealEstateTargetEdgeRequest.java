package com.youbuyfirst.backend.realestate.dto;

public record RealEstateTargetEdgeRequest(
        String fromTargetType,
        String fromTargetId,
        String toTargetType,
        String toTargetId,
        String edgeType,
        Double confidence,
        String source,
        String reviewState
) {
}
