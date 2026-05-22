package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.InvestorFlowLegRequest;
import com.youbuyfirst.backend.market.dto.InvestorFlowLegResponse;
import com.youbuyfirst.backend.market.dto.InvestorFlowSnapshotRequest;
import com.youbuyfirst.backend.market.dto.InvestorFlowSnapshotResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.util.Collection;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class InvestorFlowSnapshotService {

    private static final InvestorFlowLegResponse ZERO_LEG = new InvestorFlowLegResponse(BigDecimal.ZERO, 0);

    private final InvestorFlowSnapshotRepository repository;
    private final Duration staleAfter;

    public InvestorFlowSnapshotService(
            InvestorFlowSnapshotRepository repository,
            @Value("${app.market.investor-flow-stale-minutes:5760}") long investorFlowStaleMinutes
    ) {
        this.repository = repository;
        this.staleAfter = Duration.ofMinutes(investorFlowStaleMinutes);
    }

    @Transactional
    public void upsertAll(Collection<InvestorFlowSnapshotRequest> requests) {
        Instant collectedAt = Instant.now();
        for (InvestorFlowSnapshotRequest request : requests) {
            String symbol = normalize(request.symbol());
            InvestorFlowSnapshot snapshot = repository.findBySymbolIgnoreCase(symbol)
                    .orElseGet(() -> new InvestorFlowSnapshot(symbol));
            snapshot.update(
                    request.name().trim(),
                    normalize(request.market()),
                    normalize(request.currency()),
                    request.tradeDate(),
                    request.provider().trim(),
                    request.sourceLabel().trim(),
                    request.delayLabel().trim(),
                    request.asOf(),
                    normalize(request.dataStatus()),
                    collectedAt,
                    request.individual(),
                    request.foreign(),
                    request.institution()
            );
            repository.save(snapshot);
        }
    }

    @Transactional(readOnly = true)
    public List<InvestorFlowSnapshotResponse> list(String symbols) {
        List<String> requestedSymbols = parseSymbols(symbols);
        if (requestedSymbols.isEmpty()) {
            return repository.findAll(Sort.by("symbol")).stream()
                    .map(this::toResponse)
                    .toList();
        }

        List<String> lowerSymbols = requestedSymbols.stream()
                .map(symbol -> symbol.toLowerCase(Locale.ROOT))
                .toList();
        Map<String, InvestorFlowSnapshot> snapshotsBySymbol = repository.findBySymbolsIgnoreCase(lowerSymbols).stream()
                .collect(Collectors.toMap(
                        snapshot -> snapshot.getSymbol().toLowerCase(Locale.ROOT),
                        Function.identity(),
                        (left, right) -> left,
                        LinkedHashMap::new
                ));

        return requestedSymbols.stream()
                .map(symbol -> snapshotsBySymbol.containsKey(symbol.toLowerCase(Locale.ROOT))
                        ? toResponse(snapshotsBySymbol.get(symbol.toLowerCase(Locale.ROOT)))
                        : insufficientResponse(symbol))
                .sorted(Comparator.comparing(response -> requestedSymbols.indexOf(response.symbol())))
                .toList();
    }

    private InvestorFlowSnapshotResponse toResponse(InvestorFlowSnapshot snapshot) {
        boolean stale = isStale(snapshot);
        return new InvestorFlowSnapshotResponse(
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
                new InvestorFlowLegResponse(snapshot.getIndividualNetAmount(), snapshot.getIndividualNetVolume()),
                new InvestorFlowLegResponse(snapshot.getForeignNetAmount(), snapshot.getForeignNetVolume()),
                new InvestorFlowLegResponse(snapshot.getInstitutionNetAmount(), snapshot.getInstitutionNetVolume())
        );
    }

    private InvestorFlowSnapshotResponse insufficientResponse(String symbol) {
        String market = inferMarket(symbol);
        return new InvestorFlowSnapshotResponse(
                symbol,
                symbol,
                market,
                "KR".equals(market) ? "KRW" : "USD",
                LocalDate.EPOCH,
                "none",
                "No investor flow data",
                "Domestic previous trading day investor flow",
                Instant.EPOCH,
                true,
                "INSUFFICIENT",
                ZERO_LEG,
                ZERO_LEG,
                ZERO_LEG
        );
    }

    private boolean isStale(InvestorFlowSnapshot snapshot) {
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
                .map(InvestorFlowSnapshotService::normalize)
                .filter(symbol -> !symbol.isBlank())
                .distinct()
                .toList();
    }

    private static String normalize(String value) {
        return value == null ? "" : value.trim().toUpperCase(Locale.ROOT);
    }

    private static String inferMarket(String symbol) {
        if (symbol.endsWith(".KS") || symbol.endsWith(".KQ") || symbol.replace(".", "").chars().allMatch(Character::isDigit)) {
            return "KR";
        }
        return "US";
    }
}
