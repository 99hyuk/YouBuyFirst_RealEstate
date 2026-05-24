package com.youbuyfirst.backend.market.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChartCandleRefreshFailureRequest(
        @NotBlank
        String symbol,
        @NotBlank
        String range,
        @NotBlank
        String interval,
        @Size(max = 64)
        String refreshAttemptToken,
        String errorMessage
) {
}
