package com.youbuyfirst.backend.market.dto;

import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

public record InvestorFlowLegRequest(
        BigDecimal netAmount,
        @NotNull Long netVolume,
        Boolean derived
) {
}
