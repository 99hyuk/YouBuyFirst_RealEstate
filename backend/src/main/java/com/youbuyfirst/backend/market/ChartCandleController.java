package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.ChartCandleBatchRequest;
import com.youbuyfirst.backend.market.dto.ChartCandleResponse;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ChartCandleController {

    private final ChartCandleService chartCandleService;

    public ChartCandleController(ChartCandleService chartCandleService) {
        this.chartCandleService = chartCandleService;
    }

    @PostMapping("/internal/market/chart-candles")
    public ResponseEntity<Void> upsert(@Valid @RequestBody ChartCandleBatchRequest request) {
        chartCandleService.upsertAll(request.items());
        return ResponseEntity.ok().build();
    }

    @GetMapping("/api/market/chart-candles")
    public ChartCandleResponse chartCandles(
            @RequestParam String symbol,
            @RequestParam(required = false) String range,
            @RequestParam(required = false) String interval
    ) {
        return chartCandleService.get(symbol, range, interval);
    }
}
