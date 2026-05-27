package com.youbuyfirst.backend.admin;

import com.youbuyfirst.backend.instrument.Instrument;

import java.util.List;

public record InstrumentMatcherSnapshotView(
        Long instrumentId,
        String market,
        String symbol,
        String name,
        List<String> aliases
) {
    public static InstrumentMatcherSnapshotView from(Instrument instrument, List<String> aliases) {
        return new InstrumentMatcherSnapshotView(
                instrument.getId(),
                instrument.getMarket(),
                instrument.getSymbol(),
                displayName(instrument),
                aliases
        );
    }

    private static String displayName(Instrument instrument) {
        if (hasText(instrument.getNameKo())) {
            return instrument.getNameKo();
        }
        if (hasText(instrument.getNameEn())) {
            return instrument.getNameEn();
        }
        return instrument.getSymbol();
    }

    private static boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
