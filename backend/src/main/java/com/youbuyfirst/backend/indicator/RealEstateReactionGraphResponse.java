package com.youbuyfirst.backend.indicator;

import java.time.Instant;
import java.util.List;

public record RealEstateReactionGraphResponse(
        String targetId,
        String direction,
        String edgeType,
        String window,
        Instant windowStart,
        Instant windowEnd,
        List<RealEstateReactionGraphItemResponse> items
) {
}
