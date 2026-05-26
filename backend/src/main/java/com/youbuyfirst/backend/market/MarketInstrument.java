package com.youbuyfirst.backend.market;

public record MarketInstrument(
        Long instrumentId,
        String symbol,
        String name,
        String market,
        String currency
) {
    public MarketInstrument(String symbol, String name, String market, String currency) {
        this(null, symbol, name, market, currency);
    }
}
