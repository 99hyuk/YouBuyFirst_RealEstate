package com.youbuyfirst.backend.market.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record ChartCandleBarResponse(
        LocalDate date,
        BigDecimal open,
        BigDecimal high,
        BigDecimal low,
        BigDecimal close,
        long volume
) {
}
