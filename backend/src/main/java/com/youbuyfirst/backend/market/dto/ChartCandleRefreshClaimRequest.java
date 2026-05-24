package com.youbuyfirst.backend.market.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

public record ChartCandleRefreshClaimRequest(
        @Min(1)
        @Max(100)
        Integer limit
) {
}
