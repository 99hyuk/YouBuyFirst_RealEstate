package com.youbuyfirst.backend.market.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;

import java.math.BigDecimal;
import java.time.LocalDate;

public record ChartCandleBarRequest(
        @NotNull LocalDate date,
        @NotNull @DecimalMin(value = "0.0", inclusive = false) BigDecimal open,
        @NotNull @DecimalMin(value = "0.0", inclusive = false) BigDecimal high,
        @NotNull @DecimalMin(value = "0.0", inclusive = false) BigDecimal low,
        @NotNull @DecimalMin(value = "0.0", inclusive = false) BigDecimal close,
        @NotNull @PositiveOrZero Long volume
) {
}
