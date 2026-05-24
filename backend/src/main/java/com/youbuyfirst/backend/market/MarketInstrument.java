package com.youbuyfirst.backend.market;

public record MarketInstrument(
        String symbol,
        String name,
        String market,
        String currency
) {
}
