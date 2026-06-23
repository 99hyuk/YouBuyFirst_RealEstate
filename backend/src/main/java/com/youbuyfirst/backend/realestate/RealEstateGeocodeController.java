package com.youbuyfirst.backend.realestate;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class RealEstateGeocodeController {

    private final RealEstateGeocodeService service;

    public RealEstateGeocodeController(RealEstateGeocodeService service) {
        this.service = service;
    }

    @PostMapping("/api/realestate/geocode")
    public GeocodeResponse geocode(@RequestBody GeocodeRequest request) {
        List<String> queries = request == null || request.queries() == null ? List.of() : request.queries();
        return new GeocodeResponse(service.resolve(queries));
    }

    public record GeocodeRequest(List<String> queries) {
    }

    public record GeocodeResponse(List<RealEstateGeocodeService.GeocodeResult> results) {
    }
}
