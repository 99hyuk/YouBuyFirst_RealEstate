package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.ChartCandleRefreshClaimResponse;
import com.youbuyfirst.backend.market.dto.ChartCandleRefreshFailureRequest;
import com.youbuyfirst.backend.market.dto.ChartCandleRefreshRequestResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;

@Service
public class ChartCandleRefreshRequestService {

    private static final int DEFAULT_CLAIM_LIMIT = 20;
    private static final int MAX_CLAIM_LIMIT = 100;
    private static final Duration CLAIM_LEASE_DURATION = Duration.ofMinutes(5);
    private static final Set<String> CLAIMABLE_STATUSES = Set.of(
            ChartCandleRefreshRequest.STATUS_PENDING,
            ChartCandleRefreshRequest.STATUS_FAILED
    );

    private final ChartCandleRefreshRequestRepository repository;
    private final MarketSymbolResolver symbolResolver;

    public ChartCandleRefreshRequestService(
            ChartCandleRefreshRequestRepository repository,
            MarketSymbolResolver symbolResolver
    ) {
        this.repository = repository;
        this.symbolResolver = symbolResolver;
    }

    @Transactional
    public void request(String symbol, String range, String interval) {
        request(symbolResolver.resolve(symbol), range, interval);
    }

    @Transactional
    public void request(MarketInstrument instrument, String range, String interval) {
        Instant now = Instant.now();
        Optional<ChartCandleRefreshRequest> existingByInstrument = instrument.instrumentId() == null
                ? Optional.empty()
                : repository.findFirstByInstrumentIdAndRangeLabelAndCandleInterval(instrument.instrumentId(), range, interval);
        ChartCandleRefreshRequest request = existingByInstrument
                .or(() -> repository.findBySymbolIgnoreCaseAndRangeLabelAndCandleInterval(instrument.symbol(), range, interval))
                .orElseGet(() -> new ChartCandleRefreshRequest(instrument.instrumentId(), instrument.symbol(), range, interval, now));
        request.bindInstrument(instrument.instrumentId(), instrument.symbol());
        if (!ChartCandleRefreshRequest.STATUS_PENDING.equals(request.getStatus())
                && !request.isActiveInProgress(now, CLAIM_LEASE_DURATION)) {
            request.requestAgain(now);
        }
        repository.save(request);
    }

    @Transactional
    public ChartCandleRefreshClaimResponse claim(Integer requestedLimit) {
        int limit = Math.max(1, Math.min(requestedLimit == null ? DEFAULT_CLAIM_LIMIT : requestedLimit, MAX_CLAIM_LIMIT));
        Instant now = Instant.now();
        List<ChartCandleRefreshRequest> requests = new ArrayList<>(
                repository.findClaimable(CLAIMABLE_STATUSES, PageRequest.of(0, limit))
        );
        if (requests.size() < limit) {
            requests.addAll(repository.findTimedOutInProgress(
                    ChartCandleRefreshRequest.STATUS_IN_PROGRESS,
                    now.minus(CLAIM_LEASE_DURATION),
                    PageRequest.of(0, limit - requests.size())
            ));
        }

        List<ChartCandleRefreshRequestResponse> items = requests
                .stream()
                .peek(request -> request.claim(now))
                .map(request -> new ChartCandleRefreshRequestResponse(
                        request.getInstrumentId(),
                        request.getSymbol(),
                        request.getRangeLabel(),
                        request.getCandleInterval(),
                        request.getAttemptToken()
                ))
                .toList();
        return new ChartCandleRefreshClaimResponse(items);
    }

    @Transactional
    public boolean canAcceptCompletion(String symbol, String range, String interval, String refreshAttemptToken) {
        return canAcceptCompletion(symbolResolver.resolve(symbol), range, interval, refreshAttemptToken);
    }

    @Transactional
    public boolean canAcceptCompletion(MarketInstrument instrument, String range, String interval, String refreshAttemptToken) {
        return findLocked(instrument, range, interval)
                .map(request -> canAcceptCompletion(request, refreshAttemptToken))
                .orElse(isBlank(refreshAttemptToken));
    }

    @Transactional
    public void markCompleted(String symbol, String range, String interval, String refreshAttemptToken) {
        markCompleted(symbolResolver.resolve(symbol), range, interval, refreshAttemptToken);
    }

    @Transactional
    public void markCompleted(MarketInstrument instrument, String range, String interval, String refreshAttemptToken) {
        findLocked(instrument, range, interval)
                .filter(request -> canAcceptCompletion(request, refreshAttemptToken))
                .ifPresent(request -> request.complete(Instant.now()));
    }

    @Transactional
    public void markFailed(ChartCandleRefreshFailureRequest failureRequest) {
        if (isBlank(failureRequest.refreshAttemptToken())) {
            return;
        }
        MarketInstrument instrument = symbolResolver.resolve(failureRequest.symbol());
        findLocked(instrument, failureRequest.range(), failureRequest.interval())
                .filter(request -> request.isActiveAttempt(failureRequest.refreshAttemptToken()))
                .ifPresent(request -> request.fail(Instant.now(), failureRequest.errorMessage()));
    }

    private Optional<ChartCandleRefreshRequest> findLocked(MarketInstrument instrument, String range, String interval) {
        if (instrument.instrumentId() != null) {
            Optional<ChartCandleRefreshRequest> byInstrument = repository.findLockedByInstrumentIdAndRangeLabelAndCandleInterval(
                    instrument.instrumentId(),
                    range,
                    interval
            );
            if (byInstrument.isPresent()) {
                return byInstrument;
            }
        }
        return repository.findLockedBySymbolAndRangeLabelAndCandleInterval(instrument.symbol(), range, interval);
    }

    private static boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    private static boolean canAcceptCompletion(ChartCandleRefreshRequest request, String refreshAttemptToken) {
        if (isBlank(refreshAttemptToken)) {
            return !request.hasActiveAttemptToken();
        }
        return request.isActiveAttempt(refreshAttemptToken);
    }
}
