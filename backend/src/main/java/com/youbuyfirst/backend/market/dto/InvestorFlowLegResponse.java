package com.youbuyfirst.backend.market.dto;

import java.math.BigDecimal;

public record InvestorFlowLegResponse(
        BigDecimal netAmount,
        long netVolume
) {
}
