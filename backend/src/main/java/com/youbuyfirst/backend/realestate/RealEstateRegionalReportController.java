package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateRegionalReportBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateRegionalReportBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateRegionalReportResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateRegionalReportController {

    private final RealEstateRegionalReportService service;

    public RealEstateRegionalReportController(RealEstateRegionalReportService service) {
        this.service = service;
    }

    @PostMapping("/internal/realestate/regional-reports")
    public RealEstateRegionalReportBatchResponse upsertRegionalReports(
            @Valid @RequestBody RealEstateRegionalReportBatchRequest request
    ) {
        return service.upsertAll(request.reports());
    }

    @GetMapping("/api/realestate/targets/{targetId}/regional-report")
    public RealEstateRegionalReportResponse targetRegionalReport(@PathVariable String targetId) {
        return service.latestForTarget(targetId);
    }
}
