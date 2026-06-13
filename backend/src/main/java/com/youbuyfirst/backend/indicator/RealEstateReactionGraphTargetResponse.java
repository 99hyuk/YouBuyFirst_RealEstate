package com.youbuyfirst.backend.indicator;

public record RealEstateReactionGraphTargetResponse(
        String targetId,
        String targetType,
        String displayName,
        String slug
) {
}
