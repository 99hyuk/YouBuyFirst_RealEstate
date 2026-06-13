package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateMarketDataTargetListResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateRegionImportBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateRegionImportResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetListResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetUpsertBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetUpsertBatchResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateTargetController {

    private final RealEstateTargetService service;

    public RealEstateTargetController(RealEstateTargetService service) {
        this.service = service;
    }

    @GetMapping("/api/realestate/targets/search")
    public RealEstateTargetListResponse search(
            @RequestParam(required = false) String q,
            @RequestParam(defaultValue = "20") int limit
    ) {
        return new RealEstateTargetListResponse(service.search(q, limit));
    }

    @GetMapping("/internal/realestate/market-data-targets")
    public RealEstateMarketDataTargetListResponse marketDataTargets(
            @RequestParam(required = false) Boolean enabled,
            @RequestParam(defaultValue = "100") int limit
    ) {
        return new RealEstateMarketDataTargetListResponse(service.marketDataTargets(enabled, limit));
    }

    @PostMapping("/internal/realestate/targets")
    public RealEstateTargetUpsertBatchResponse upsertTargets(@RequestBody RealEstateTargetUpsertBatchRequest request) {
        return service.upsertTargets(request.items());
    }

    @PostMapping("/internal/realestate/regions")
    public RealEstateRegionImportResponse importRegions(@RequestBody RealEstateRegionImportBatchRequest request) {
        return service.importRegions(request.items());
    }
}
