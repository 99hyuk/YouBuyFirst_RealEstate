package com.youbuyfirst.backend.market.dto;

public record ChartCandleDisplayPolicyResponse(
        boolean displayOnly,
        boolean rawMinute,
        boolean downloadable,
        int maxBars
) {
}
