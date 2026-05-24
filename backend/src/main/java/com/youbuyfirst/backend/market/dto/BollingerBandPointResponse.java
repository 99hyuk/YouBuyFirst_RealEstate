package com.youbuyfirst.backend.market.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record BollingerBandPointResponse(
        LocalDate date,
        BigDecimal upper,
        BigDecimal middle,
        BigDecimal lower
) {
}
