package com.youbuyfirst.backend.realestate.dto;

public record RealEstateAliasResponse(
        Long aliasId,
        String targetType,
        String targetId,
        String alias,
        String normalizedAlias,
        String aliasType,
        String source,
        String evidenceUrl,
        Double confidence,
        String reviewState,
        String createdBy,
        Boolean ambiguous
) {
}
