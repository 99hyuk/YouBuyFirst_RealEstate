package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.QuoteSnapshotRequest;
import com.youbuyfirst.backend.market.dto.QuoteSnapshotResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.Instant;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class QuoteSnapshotService {

    private final QuoteSnapshotRepository repository;
    private final MarketSymbolResolver symbolResolver;
    private final Duration staleAfter;

    public QuoteSnapshotService(
            QuoteSnapshotRepository repository,
            MarketSymbolResolver symbolResolver,
            @Value("${app.market.quote-stale-minutes:30}") long quoteStaleMinutes
    ) {
        this.repository = repository;
        this.symbolResolver = symbolResolver;
        this.staleAfter = Duration.ofMinutes(quoteStaleMinutes);
    }

    @Transactional
    public void upsertAll(Collection<QuoteSnapshotRequest> requests) {
        Instant collectedAt = Instant.now();
        for (QuoteSnapshotRequest request : requests) {
            MarketInstrument instrument = symbolResolver.resolve(request.symbol());
            QuoteSnapshot snapshot = findExisting(instrument)
                    .orElseGet(() -> new QuoteSnapshot(instrument.instrumentId(), instrument.symbol()));
            snapshot.update(
                    instrument.instrumentId(),
                    request.name().trim(),
                    normalize(request.market()),
                    normalize(request.currency()),
                    request.price(),
                    request.change(),
                    request.changePct(),
                    request.volume(),
                    request.asOf(),
                    request.provider().trim(),
                    request.delayLabel().trim(),
                    normalize(request.dataStatus()),
                    collectedAt
            );
            repository.save(snapshot);
        }
    }

    @Transactional(readOnly = true)
    public List<QuoteSnapshotResponse> list(String symbols) {
        List<String> requestedSymbols = parseSymbols(symbols);
        if (requestedSymbols.isEmpty()) {
            return repository.findAll(Sort.by("symbol")).stream()
                    .map(this::toResponse)
                    .toList();
        }

        List<MarketInstrument> requestedInstruments = requestedSymbols.stream()
                .map(symbolResolver::resolve)
                .toList();
        List<Long> instrumentIds = requestedInstruments.stream()
                .map(MarketInstrument::instrumentId)
                .filter(id -> id != null)
                .distinct()
                .toList();
        Map<Long, QuoteSnapshot> snapshotsByInstrumentId = repository.findByInstrumentIdIn(instrumentIds).stream()
                .collect(Collectors.toMap(
                        QuoteSnapshot::getInstrumentId,
                        Function.identity(),
                        (left, right) -> left,
                        LinkedHashMap::new
                ));
        List<String> lowerSymbols = requestedInstruments.stream()
                .map(MarketInstrument::symbol)
                .map(symbol -> symbol.toLowerCase(Locale.ROOT))
                .distinct()
                .toList();
        Map<String, QuoteSnapshot> snapshotsBySymbol = repository.findBySymbolsIgnoreCase(lowerSymbols).stream()
                .collect(Collectors.toMap(
                        snapshot -> snapshot.getSymbol().toLowerCase(Locale.ROOT),
                        Function.identity(),
                        (left, right) -> left,
                        LinkedHashMap::new
                ));

        return requestedInstruments.stream()
                .map(instrument -> snapshotFor(instrument, snapshotsByInstrumentId, snapshotsBySymbol))
                .filter(snapshot -> snapshot != null)
                .map(this::toResponse)
                .toList();
    }

    private QuoteSnapshotResponse toResponse(QuoteSnapshot snapshot) {
        boolean stale = isStale(snapshot);
        return new QuoteSnapshotResponse(
                snapshot.getInstrumentId(),
                snapshot.getSymbol(),
                snapshot.getName(),
                snapshot.getMarket(),
                snapshot.getCurrency(),
                snapshot.getPrice(),
                snapshot.getChange(),
                snapshot.getChangePct(),
                snapshot.getVolume(),
                snapshot.getAsOf(),
                snapshot.getProvider(),
                snapshot.getDelayLabel(),
                stale,
                stale ? "STALE" : snapshot.getDataStatus()
        );
    }

    private boolean isStale(QuoteSnapshot snapshot) {
        if ("STALE".equalsIgnoreCase(snapshot.getDataStatus())) {
            return true;
        }
        return snapshot.getAsOf().plus(staleAfter).isBefore(Instant.now());
    }

    private Optional<QuoteSnapshot> findExisting(MarketInstrument instrument) {
        if (instrument.instrumentId() != null) {
            Optional<QuoteSnapshot> byInstrument = repository.findFirstByInstrumentId(instrument.instrumentId());
            if (byInstrument.isPresent()) {
                return byInstrument;
            }
        }
        return repository.findBySymbolIgnoreCase(instrument.symbol());
    }

    private QuoteSnapshot snapshotFor(
            MarketInstrument instrument,
            Map<Long, QuoteSnapshot> snapshotsByInstrumentId,
            Map<String, QuoteSnapshot> snapshotsBySymbol
    ) {
        if (instrument.instrumentId() != null) {
            QuoteSnapshot snapshot = snapshotsByInstrumentId.get(instrument.instrumentId());
            if (snapshot != null) {
                return snapshot;
            }
        }
        return snapshotsBySymbol.get(instrument.symbol().toLowerCase(Locale.ROOT));
    }

    private static List<String> parseSymbols(String symbols) {
        if (symbols == null || symbols.isBlank()) {
            return List.of();
        }
        return List.of(symbols.split(",")).stream()
                .map(QuoteSnapshotService::normalize)
                .filter(symbol -> !symbol.isBlank())
                .distinct()
                .toList();
    }

    private static String normalize(String value) {
        return value == null ? "" : value.trim().toUpperCase(Locale.ROOT);
    }
}
