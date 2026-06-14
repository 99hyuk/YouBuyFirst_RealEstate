package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerRefreshRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerRefreshResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateMapLayerController {

    private final RealEstateMapLayerService service;

    public RealEstateMapLayerController(RealEstateMapLayerService service) {
        this.service = service;
    }

    @GetMapping("/api/realestate/map/layers")
    public RealEstateMapLayerResponse latestLayer(
            @RequestParam(defaultValue = "sido") String layerType,
            @RequestParam(required = false) String parentTargetId
    ) {
        return service.latestLayer(layerType, parentTargetId);
    }

    @PostMapping("/internal/realestate/map/layer-snapshots/refresh")
    public RealEstateMapLayerRefreshResponse refreshSnapshots(
            @Valid @RequestBody RealEstateMapLayerRefreshRequest request
    ) {
        return service.refreshSnapshots(request);
    }
}
