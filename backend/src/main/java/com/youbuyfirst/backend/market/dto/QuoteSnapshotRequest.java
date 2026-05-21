package com.youbuyfirst.backend.market.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;
import java.time.Instant;

public record QuoteSnapshotRequest(
        @NotBlank @Size(max = 40) String symbol,
        @NotBlank @Size(max = 200) String name,
        @NotBlank @Size(max = 20) String market,
        @NotBlank @Size(max = 10) String currency,
        @NotNull @DecimalMin(value = "0.0", inclusive = false) BigDecimal price,
        @NotNull BigDecimal change,
        @NotNull BigDecimal changePct,
        @NotNull @PositiveOrZero Long volume,
        @NotNull Instant asOf,
        @NotBlank @Size(max = 100) String provider,
        @NotBlank @Size(max = 120) String delayLabel,
        @NotBlank @Size(max = 30) String dataStatus
) {
}
