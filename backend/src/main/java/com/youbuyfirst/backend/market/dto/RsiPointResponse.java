package com.youbuyfirst.backend.market.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record RsiPointResponse(
        LocalDate date,
        BigDecimal value
) {
}
