package com.youbuyfirst.backend.market.dto;

public record ChartCandleRefreshRequestResponse(
        Long instrumentId,
        String symbol,
        String range,
        String interval,
        String refreshAttemptToken
) {
}
