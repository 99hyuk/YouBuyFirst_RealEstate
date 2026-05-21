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
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class QuoteSnapshotService {

    private final QuoteSnapshotRepository repository;
    private final Duration staleAfter;

    public QuoteSnapshotService(
            QuoteSnapshotRepository repository,
            @Value("${app.market.quote-stale-minutes:2160}") long quoteStaleMinutes
    ) {
        this.repository = repository;
        this.staleAfter = Duration.ofMinutes(quoteStaleMinutes);
    }

    @Transactional
    public void upsertAll(Collection<QuoteSnapshotRequest> requests) {
        Instant collectedAt = Instant.now();
        for (QuoteSnapshotRequest request : requests) {
            String symbol = normalize(request.symbol());
            QuoteSnapshot snapshot = repository.findBySymbolIgnoreCase(symbol)
                    .orElseGet(() -> new QuoteSnapshot(symbol));
            snapshot.update(
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

        List<String> lowerSymbols = requestedSymbols.stream()
                .map(symbol -> symbol.toLowerCase(Locale.ROOT))
                .toList();
        Map<String, QuoteSnapshot> snapshotsBySymbol = repository.findBySymbolsIgnoreCase(lowerSymbols).stream()
                .collect(Collectors.toMap(
                        snapshot -> snapshot.getSymbol().toLowerCase(Locale.ROOT),
                        Function.identity(),
                        (left, right) -> left,
                        LinkedHashMap::new
                ));

        return requestedSymbols.stream()
                .map(symbol -> snapshotsBySymbol.get(symbol.toLowerCase(Locale.ROOT)))
                .filter(snapshot -> snapshot != null)
                .map(this::toResponse)
                .sorted(Comparator.comparing(response -> requestedSymbols.indexOf(response.symbol())))
                .toList();
    }

    private QuoteSnapshotResponse toResponse(QuoteSnapshot snapshot) {
        boolean stale = isStale(snapshot);
        return new QuoteSnapshotResponse(
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
