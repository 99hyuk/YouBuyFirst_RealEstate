package com.youbuyfirst.backend.admin;

import com.youbuyfirst.backend.instrument.Instrument;
import com.youbuyfirst.backend.instrument.InstrumentAliasRepository;
import com.youbuyfirst.backend.instrument.InstrumentAliasSnapshotRow;
import com.youbuyfirst.backend.instrument.InstrumentRepository;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class InstrumentMatcherSnapshotService {

    private final InstrumentRepository instrumentRepository;
    private final InstrumentAliasRepository instrumentAliasRepository;

    public InstrumentMatcherSnapshotService(
            InstrumentRepository instrumentRepository,
            InstrumentAliasRepository instrumentAliasRepository
    ) {
        this.instrumentRepository = instrumentRepository;
        this.instrumentAliasRepository = instrumentAliasRepository;
    }

    public List<InstrumentMatcherSnapshotView> snapshot(String market) {
        String normalizedMarket = normalizeMarket(market);
        List<Instrument> instruments = normalizedMarket == null
                ? instrumentRepository.findByOrderByMarketAscSymbolAsc()
                : instrumentRepository.findByMarketIgnoreCaseOrderByMarketAscSymbolAsc(normalizedMarket);
        Map<Long, List<String>> aliasesByInstrumentId = acceptedAliasesByInstrumentId(normalizedMarket);
        return instruments.stream()
                .map(instrument -> InstrumentMatcherSnapshotView.from(
                        instrument,
                        aliasesByInstrumentId.getOrDefault(instrument.getId(), List.of())
                ))
                .toList();
    }

    private Map<Long, List<String>> acceptedAliasesByInstrumentId(String market) {
        Map<Long, List<String>> aliasesByInstrumentId = new LinkedHashMap<>();
        for (InstrumentAliasSnapshotRow row : instrumentAliasRepository.findMatcherSnapshotAliases(market)) {
            aliasesByInstrumentId.computeIfAbsent(row.instrumentId(), ignored -> new ArrayList<>()).add(row.alias());
        }
        return aliasesByInstrumentId;
    }

    private static String normalizeMarket(String market) {
        if (market == null || market.isBlank()) {
            return null;
        }
        return market.trim().toUpperCase();
    }
}
