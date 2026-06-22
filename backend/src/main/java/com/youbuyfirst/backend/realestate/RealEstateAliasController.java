package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateAliasBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateAliasBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateAliasListResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateAliasController {

    private final RealEstateAliasService service;

    public RealEstateAliasController(RealEstateAliasService service) {
        this.service = service;
    }

    @PostMapping({
            "/internal/realestate/aliases",
            "/internal/realestate/aliases/candidates"
    })
    public RealEstateAliasBatchResponse upsertAliases(@RequestBody RealEstateAliasBatchRequest request) {
        return service.upsertAliases(request.items());
    }

    @GetMapping("/api/realestate/targets/{targetId}/aliases")
    public RealEstateAliasListResponse publicAliasesForTarget(@PathVariable String targetId) {
        return new RealEstateAliasListResponse(service.publicAliasesForTarget(targetId));
    }

    @GetMapping("/internal/realestate/aliases")
    public RealEstateAliasListResponse aliasesForExport(
            @RequestParam(required = false) String targetType,
            @RequestParam(required = false) String reviewState,
            @RequestParam(required = false) Boolean ambiguous,
            @RequestParam(defaultValue = "500") int limit,
            @RequestParam(defaultValue = "0") int page
    ) {
        return new RealEstateAliasListResponse(service.aliasesForExport(targetType, reviewState, ambiguous, limit, page));
    }
}
