package com.youbuyfirst.backend.market.dto;

import jakarta.validation.constraints.NotBlank;

public record ChartCandleRefreshFailureRequest(
        @NotBlank
        String symbol,
        @NotBlank
        String range,
        @NotBlank
        String interval,
        String errorMessage
) {
}
