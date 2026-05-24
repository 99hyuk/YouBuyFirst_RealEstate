package com.youbuyfirst.backend.admin;

import com.youbuyfirst.backend.instrument.Instrument;
import com.youbuyfirst.backend.instrument.InstrumentAlias;

import java.time.Instant;

public record InstrumentAliasView(
        Long id,
        Long instrumentId,
        String market,
        String symbol,
        String alias,
        String normalizedAlias,
        String source,
        Double confidence,
        String status,
        Boolean ambiguous,
        String notes,
        Instant createdAt,
        Instant updatedAt
) {
    public static InstrumentAliasView from(InstrumentAlias alias) {
        Instrument instrument = alias.getInstrument();
        return new InstrumentAliasView(
                alias.getId(),
                instrument.getId(),
                instrument.getMarket(),
                instrument.getSymbol(),
                alias.getAlias(),
                alias.getNormalizedAlias(),
                alias.getSource(),
                alias.getConfidence(),
                alias.getStatus(),
                alias.getAmbiguous(),
                alias.getNotes(),
                alias.getCreatedAt(),
                alias.getUpdatedAt()
        );
    }
}
