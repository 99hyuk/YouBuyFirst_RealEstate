package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateComplexBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateComplexBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateNearbyComplexListResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateComplexController {

    private final RealEstateComplexService service;

    public RealEstateComplexController(RealEstateComplexService service) {
        this.service = service;
    }

    @GetMapping("/api/realestate/targets/{targetId}/nearby-complexes")
    public RealEstateNearbyComplexListResponse nearbyComplexes(
            @PathVariable String targetId,
            @RequestParam(defaultValue = "20") int limit
    ) {
        return service.nearbyComplexes(targetId, limit);
    }

    @PostMapping("/internal/realestate/complexes")
    public RealEstateComplexBatchResponse upsertComplexes(@RequestBody RealEstateComplexBatchRequest request) {
        return service.upsertComplexes(request.items());
    }
}
