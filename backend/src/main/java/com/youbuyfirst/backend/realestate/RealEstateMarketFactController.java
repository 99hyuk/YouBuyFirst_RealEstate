package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateMarketFactBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketFactBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketFactListResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketSummaryResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateMarketFactController {

    private final RealEstateMarketFactService service;

    public RealEstateMarketFactController(RealEstateMarketFactService service) {
        this.service = service;
    }

    @PostMapping("/internal/realestate/market-facts")
    public RealEstateMarketFactBatchResponse upsert(@Valid @RequestBody RealEstateMarketFactBatchRequest request) {
        return new RealEstateMarketFactBatchResponse(service.upsertAll(request.items()));
    }

    @GetMapping("/api/realestate/market-facts")
    public RealEstateMarketFactListResponse list(
            @RequestParam(required = false) String targetId,
            @RequestParam(required = false) String legalDongCode,
            @RequestParam(required = false) String factType,
            @RequestParam(defaultValue = "100") int limit,
            @RequestParam(defaultValue = "0") int page
    ) {
        return new RealEstateMarketFactListResponse(service.list(targetId, legalDongCode, factType, limit, page));
    }

    @GetMapping("/api/realestate/targets/{targetId}/market-facts")
    public RealEstateMarketFactListResponse listForTarget(
            @PathVariable String targetId,
            @RequestParam(required = false) String factType,
            @RequestParam(defaultValue = "100") int limit,
            @RequestParam(defaultValue = "false") boolean officialOnly
    ) {
        return new RealEstateMarketFactListResponse(service.listForTarget(targetId, factType, limit, officialOnly));
    }

    @GetMapping("/api/realestate/dashboard/market-summary")
    public RealEstateMarketSummaryResponse marketSummary(
            @RequestParam(required = false) String legalDongCode
    ) {
        return service.summarizeForDashboard(legalDongCode);
    }
}
