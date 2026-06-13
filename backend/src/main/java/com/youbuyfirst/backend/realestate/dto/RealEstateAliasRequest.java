package com.youbuyfirst.backend.realestate.dto;

public record RealEstateAliasRequest(
        String targetType,
        String targetId,
        String alias,
        String aliasType,
        String source,
        String evidenceUrl,
        Double confidence,
        String reviewState,
        String createdBy,
        Boolean ambiguous
) {
}
