package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.InvestorFlowLegRequest;
import com.youbuyfirst.backend.market.dto.InvestorFlowLegResponse;
import com.youbuyfirst.backend.market.dto.InvestorFlowSnapshotRequest;
import com.youbuyfirst.backend.market.dto.InvestorFlowSnapshotResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Optional;

@Service
public class InvestorFlowSnapshotService {

    private static final List<String> PUBLIC_HISTORY_STATUSES = List.of("OK", "STALE");
    private static final int DEFAULT_LIMIT = 20;
    private static final int MAX_LIMIT = 120;

    private final InvestorFlowSnapshotRepository repository;
    private final MarketSymbolResolver symbolResolver;
    private final Duration staleAfter;

    public InvestorFlowSnapshotService(
            InvestorFlowSnapshotRepository repository,
            MarketSymbolResolver symbolResolver,
            @Value("${app.market.investor-flow-stale-minutes:5760}") long investorFlowStaleMinutes
    ) {
        this.repository = repository;
        this.symbolResolver = symbolResolver;
        this.staleAfter = Duration.ofMinutes(investorFlowStaleMinutes);
    }

    @Transactional
    public void upsertAll(Collection<InvestorFlowSnapshotRequest> requests) {
        Instant collectedAt = Instant.now();
        for (InvestorFlowSnapshotRequest request : requests) {
            String dataStatus = normalize(request.dataStatus());
            if (!PUBLIC_HISTORY_STATUSES.contains(dataStatus)) {
                continue;
            }
            MarketInstrument instrument = symbolResolver.resolve(request.symbol());
            InvestorFlowSnapshot snapshot = findExisting(instrument, request.tradeDate())
                    .orElseGet(() -> new InvestorFlowSnapshot(instrument.instrumentId(), instrument.symbol()));
            snapshot.update(
                    instrument.instrumentId(),
                    request.name().trim(),
                    normalize(request.market()),
                    normalize(request.currency()),
                    request.tradeDate(),
                    request.provider().trim(),
                    request.sourceLabel().trim(),
                    request.delayLabel().trim(),
                    request.asOf(),
                    dataStatus,
                    collectedAt,
                    request.individual(),
                    request.foreign(),
                    request.institution()
            );
            repository.save(snapshot);
        }
    }

    @Transactional(readOnly = true)
    public List<InvestorFlowSnapshotResponse> history(String symbol, Integer limit) {
        MarketInstrument instrument = symbolResolver.resolve(symbol);
        List<InvestorFlowSnapshot> snapshots = instrument.instrumentId() == null
                ? repository.findBySymbolIgnoreCaseAndDataStatusInOrderByTradeDateDesc(
                        instrument.symbol(),
                        PUBLIC_HISTORY_STATUSES,
                        PageRequest.of(0, boundedLimit(limit))
                )
                : repository.findByInstrumentIdAndDataStatusInOrderByTradeDateDesc(
                        instrument.instrumentId(),
                        PUBLIC_HISTORY_STATUSES,
                        PageRequest.of(0, boundedLimit(limit))
                );
        return snapshots.stream()
                .filter(snapshot -> PUBLIC_HISTORY_STATUSES.contains(normalize(snapshot.getDataStatus())))
                .map(this::toResponse)
                .toList();
    }

    private InvestorFlowSnapshotResponse toResponse(InvestorFlowSnapshot snapshot) {
        boolean stale = isStale(snapshot);
        return new InvestorFlowSnapshotResponse(
                snapshot.getInstrumentId(),
                snapshot.getSymbol(),
                snapshot.getName(),
                snapshot.getMarket(),
                snapshot.getCurrency(),
                snapshot.getTradeDate(),
                snapshot.getProvider(),
                snapshot.getSourceLabel(),
                snapshot.getDelayLabel(),
                snapshot.getAsOf(),
                stale,
                stale ? "STALE" : snapshot.getDataStatus(),
                new InvestorFlowLegResponse(
                        snapshot.getIndividualNetAmount(),
                        snapshot.getIndividualNetVolume(),
                        snapshot.isIndividualDerived()
                ),
                new InvestorFlowLegResponse(
                        snapshot.getForeignNetAmount(),
                        snapshot.getForeignNetVolume(),
                        snapshot.isForeignDerived()
                ),
                new InvestorFlowLegResponse(
                        snapshot.getInstitutionNetAmount(),
                        snapshot.getInstitutionNetVolume(),
                        snapshot.isInstitutionDerived()
                )
        );
    }

    private boolean isStale(InvestorFlowSnapshot snapshot) {
        if ("STALE".equalsIgnoreCase(snapshot.getDataStatus())) {
            return true;
        }
        return snapshot.getAsOf().plus(staleAfter).isBefore(Instant.now());
    }

    private Optional<InvestorFlowSnapshot> findExisting(MarketInstrument instrument, java.time.LocalDate tradeDate) {
        if (instrument.instrumentId() != null) {
            Optional<InvestorFlowSnapshot> byInstrument = repository.findFirstByInstrumentIdAndTradeDate(
                    instrument.instrumentId(),
                    tradeDate
            );
            if (byInstrument.isPresent()) {
                return byInstrument;
            }
        }
        return repository.findBySymbolIgnoreCaseAndTradeDate(instrument.symbol(), tradeDate);
    }

    private static int boundedLimit(Integer limit) {
        if (limit == null) {
            return DEFAULT_LIMIT;
        }
        return Math.max(1, Math.min(limit, MAX_LIMIT));
    }

    private static String normalize(String value) {
        return value == null ? "" : value.trim().toUpperCase(Locale.ROOT);
    }
}
