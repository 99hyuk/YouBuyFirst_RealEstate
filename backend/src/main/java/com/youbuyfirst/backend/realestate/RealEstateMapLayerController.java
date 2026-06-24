package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerRefreshRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerRefreshResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMapLayerResponse;
import com.youbuyfirst.backend.realestate.batch.RealEstateBatchUpdateEvent;
import com.youbuyfirst.backend.realestate.batch.RealEstateBatchUpdatePublisher;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;

@RestController
public class RealEstateMapLayerController {

    private static final String MAP_LAYERS_TOPIC = "map-layers";

    private final RealEstateMapLayerService service;
    private final RealEstateBatchUpdatePublisher updatePublisher;

    public RealEstateMapLayerController(
            RealEstateMapLayerService service,
            RealEstateBatchUpdatePublisher updatePublisher
    ) {
        this.service = service;
        this.updatePublisher = updatePublisher;
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
        RealEstateMapLayerRefreshResponse response = service.refreshSnapshots(request);
        updatePublisher.publish(new RealEstateBatchUpdateEvent(
                MAP_LAYERS_TOPIC,
                null,
                response.acceptedSnapshots(),
                Instant.now()
        ));
        return response;
    }
}
