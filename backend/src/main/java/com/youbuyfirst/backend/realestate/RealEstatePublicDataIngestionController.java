package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataImportRunListResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataPromoteRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataPromoteResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataRawIngestionBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataRawIngestionResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class RealEstatePublicDataIngestionController {

    private final RealEstatePublicDataIngestionService service;

    public RealEstatePublicDataIngestionController(RealEstatePublicDataIngestionService service) {
        this.service = service;
    }

    @PostMapping("/internal/realestate/public-data/raw-ingestions")
    public RealEstatePublicDataRawIngestionResponse ingest(
            @Valid @RequestBody RealEstatePublicDataRawIngestionBatchRequest request
    ) {
        return service.ingest(request);
    }

    @PostMapping("/internal/realestate/public-data/promote-staging")
    public RealEstatePublicDataPromoteResponse promoteStaging(
            @Valid @RequestBody RealEstatePublicDataPromoteRequest request
    ) {
        return service.promoteStaging(request);
    }

    @GetMapping("/internal/realestate/public-data/import-runs")
    public RealEstatePublicDataImportRunListResponse listRuns(
            @RequestParam(required = false) String providerDataset,
            @RequestParam(required = false) String status,
            @RequestParam(required = false, name = "runKey") List<String> runKeys,
            @RequestParam(defaultValue = "100") int limit
    ) {
        return new RealEstatePublicDataImportRunListResponse(
                service.listRuns(providerDataset, status, runKeys, limit)
        );
    }
}
