package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateIndicatorOverviewResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateIndicatorController {

    private final RealEstateIndicatorService service;

    public RealEstateIndicatorController(RealEstateIndicatorService service) {
        this.service = service;
    }

    @GetMapping("/api/realestate/indicators")
    public RealEstateIndicatorOverviewResponse overview(
            @RequestParam(required = false) String legalDongCode,
            @RequestParam(required = false) String period
    ) {
        return service.overview(legalDongCode, period);
    }
}
