package com.youbuyfirst.backend.market.dto;

import java.math.BigDecimal;
import java.util.List;

public record BollingerBandsResponse(
        int period,
        BigDecimal multiplier,
        List<BollingerBandPointResponse> points
) {
}
