package com.youbuyfirst.backend.market.dto;

import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

public record InvestorFlowLegRequest(
        @NotNull BigDecimal netAmount,
        @NotNull Long netVolume
) {
}
