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

    public ChartCandleRefreshRequestService(ChartCandleRefreshRequestRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public void request(String symbol, String range, String interval) {
        Instant now = Instant.now();
        ChartCandleRefreshRequest request = repository
                .findBySymbolIgnoreCaseAndRangeLabelAndCandleInterval(symbol, range, interval)
                .orElseGet(() -> new ChartCandleRefreshRequest(symbol, range, interval, now));
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
        return repository.findLockedBySymbolAndRangeLabelAndCandleInterval(symbol, range, interval)
                .map(request -> canAcceptCompletion(request, refreshAttemptToken))
                .orElse(isBlank(refreshAttemptToken));
    }

    @Transactional
    public void markCompleted(String symbol, String range, String interval, String refreshAttemptToken) {
        repository.findLockedBySymbolAndRangeLabelAndCandleInterval(symbol, range, interval)
                .filter(request -> canAcceptCompletion(request, refreshAttemptToken))
                .ifPresent(request -> request.complete(Instant.now()));
    }

    @Transactional
    public void markFailed(ChartCandleRefreshFailureRequest failureRequest) {
        if (isBlank(failureRequest.refreshAttemptToken())) {
            return;
        }
        repository.findLockedBySymbolAndRangeLabelAndCandleInterval(
                        failureRequest.symbol(),
                        failureRequest.range(),
                        failureRequest.interval()
                )
                .filter(request -> request.isActiveAttempt(failureRequest.refreshAttemptToken()))
                .ifPresent(request -> request.fail(Instant.now(), failureRequest.errorMessage()));
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
