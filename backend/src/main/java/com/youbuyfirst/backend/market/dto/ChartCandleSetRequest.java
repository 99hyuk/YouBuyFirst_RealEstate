package com.youbuyfirst.backend.market.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.util.List;

public record ChartCandleSetRequest(
        @NotBlank @Size(max = 40) String symbol,
        @NotBlank @Size(max = 200) String name,
        @NotBlank @Size(max = 20) String market,
        @NotBlank @Size(max = 10) String currency,
        @NotBlank @Size(max = 10) String range,
        @NotBlank @Size(max = 10) String interval,
        @NotBlank @Size(max = 100) String provider,
        @NotBlank @Size(max = 120) String delayLabel,
        @NotNull Instant asOf,
        @NotBlank @Size(max = 30) String dataStatus,
        @NotNull List<@Valid ChartCandleBarRequest> bars,
        @Size(max = 64) String refreshAttemptToken
) {
}
