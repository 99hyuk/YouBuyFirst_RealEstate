package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateEvidenceLogBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateEvidenceLogBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateEvidenceLogListResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateEvidenceLogController {

    private final RealEstateEvidenceLogService service;

    public RealEstateEvidenceLogController(RealEstateEvidenceLogService service) {
        this.service = service;
    }

    @PostMapping("/internal/realestate/evidence-logs")
    public RealEstateEvidenceLogBatchResponse upsertEvidenceLogs(
            @Valid @RequestBody RealEstateEvidenceLogBatchRequest request
    ) {
        return service.upsertAll(request.logs());
    }

    @GetMapping("/api/realestate/targets/{targetId}/evidence-logs")
    public RealEstateEvidenceLogListResponse targetEvidenceLogs(
            @PathVariable String targetId,
            @RequestParam(defaultValue = "10") int limit
    ) {
        return new RealEstateEvidenceLogListResponse(service.listForTarget(targetId, limit));
    }
}
