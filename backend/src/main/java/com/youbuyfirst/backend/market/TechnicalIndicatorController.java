package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.TechnicalIndicatorResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;

@RestController
public class TechnicalIndicatorController {

    private final TechnicalIndicatorService technicalIndicatorService;

    public TechnicalIndicatorController(TechnicalIndicatorService technicalIndicatorService) {
        this.technicalIndicatorService = technicalIndicatorService;
    }

    @GetMapping("/api/market/technical-indicators")
    public TechnicalIndicatorResponse technicalIndicators(
            @RequestParam String symbol,
            @RequestParam(required = false) String range,
            @RequestParam(required = false) String interval,
            @RequestParam(required = false) Integer rsiPeriod,
            @RequestParam(required = false) Integer bollingerPeriod,
            @RequestParam(required = false) BigDecimal bollingerMultiplier
    ) {
        return technicalIndicatorService.get(
                symbol,
                range,
                interval,
                rsiPeriod,
                bollingerPeriod,
                bollingerMultiplier
        );
    }
}
