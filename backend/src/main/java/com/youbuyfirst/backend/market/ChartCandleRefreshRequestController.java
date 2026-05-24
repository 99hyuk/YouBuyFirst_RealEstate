package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.ChartCandleRefreshClaimRequest;
import com.youbuyfirst.backend.market.dto.ChartCandleRefreshClaimResponse;
import com.youbuyfirst.backend.market.dto.ChartCandleRefreshFailureRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ChartCandleRefreshRequestController {

    private final ChartCandleRefreshRequestService refreshRequestService;

    public ChartCandleRefreshRequestController(ChartCandleRefreshRequestService refreshRequestService) {
        this.refreshRequestService = refreshRequestService;
    }

    @PostMapping("/internal/market/chart-candle-refresh-requests/claim")
    public ChartCandleRefreshClaimResponse claim(@RequestBody(required = false) ChartCandleRefreshClaimRequest request) {
        return refreshRequestService.claim(request == null ? null : request.limit());
    }

    @PostMapping("/internal/market/chart-candle-refresh-requests/fail")
    public ResponseEntity<Void> fail(@Valid @RequestBody ChartCandleRefreshFailureRequest request) {
        refreshRequestService.markFailed(request);
        return ResponseEntity.ok().build();
    }
}
