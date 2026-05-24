package com.youbuyfirst.backend.market.dto;

public record ChartCandleRefreshRequestResponse(
        String symbol,
        String range,
        String interval,
        String refreshAttemptToken
) {
}
