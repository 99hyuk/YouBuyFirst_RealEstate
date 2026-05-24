package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.ChartCandleRefreshClaimResponse;
import com.youbuyfirst.backend.market.dto.ChartCandleRefreshFailureRequest;
import com.youbuyfirst.backend.market.dto.ChartCandleRefreshRequestResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Set;

@Service
public class ChartCandleRefreshRequestService {

    private static final int DEFAULT_CLAIM_LIMIT = 20;
    private static final int MAX_CLAIM_LIMIT = 100;
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
                && !ChartCandleRefreshRequest.STATUS_IN_PROGRESS.equals(request.getStatus())) {
            request.requestAgain(now);
        }
        repository.save(request);
    }

    @Transactional
    public ChartCandleRefreshClaimResponse claim(Integer requestedLimit) {
        int limit = Math.max(1, Math.min(requestedLimit == null ? DEFAULT_CLAIM_LIMIT : requestedLimit, MAX_CLAIM_LIMIT));
        Instant now = Instant.now();
        List<ChartCandleRefreshRequestResponse> items = repository
                .findClaimable(CLAIMABLE_STATUSES, PageRequest.of(0, limit))
                .stream()
                .peek(request -> request.claim(now))
                .map(request -> new ChartCandleRefreshRequestResponse(
                        request.getSymbol(),
                        request.getRangeLabel(),
                        request.getCandleInterval()
                ))
                .toList();
        return new ChartCandleRefreshClaimResponse(items);
    }

    @Transactional
    public void markCompleted(String symbol, String range, String interval) {
        repository.findBySymbolIgnoreCaseAndRangeLabelAndCandleInterval(symbol, range, interval)
                .ifPresent(request -> request.complete(Instant.now()));
    }

    @Transactional
    public void markFailed(ChartCandleRefreshFailureRequest failureRequest) {
        repository.findBySymbolIgnoreCaseAndRangeLabelAndCandleInterval(
                        failureRequest.symbol(),
                        failureRequest.range(),
                        failureRequest.interval()
                )
                .ifPresent(request -> request.fail(Instant.now(), failureRequest.errorMessage()));
    }
}
