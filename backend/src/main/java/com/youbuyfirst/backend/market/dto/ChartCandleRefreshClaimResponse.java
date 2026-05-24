package com.youbuyfirst.backend.market.dto;

import java.util.List;

public record ChartCandleRefreshClaimResponse(
        List<ChartCandleRefreshRequestResponse> items
) {
}
