package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateTargetEdgeBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetEdgeBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetEdgeGraphResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetEdgeListResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateTargetGraphController {

    private final RealEstateTargetGraphService service;

    public RealEstateTargetGraphController(RealEstateTargetGraphService service) {
        this.service = service;
    }

    @PostMapping("/internal/realestate/target-edges")
    public RealEstateTargetEdgeBatchResponse upsertEdges(@RequestBody RealEstateTargetEdgeBatchRequest request) {
        return service.upsertEdges(request.items());
    }

    @GetMapping("/api/realestate/targets/{targetId}/graph")
    public RealEstateTargetEdgeGraphResponse publicGraph(
            @PathVariable String targetId,
            @RequestParam(defaultValue = "both") String direction,
            @RequestParam(required = false) String edgeType,
            @RequestParam(defaultValue = "200") int limit
    ) {
        String normalizedDirection = normalizeDirection(direction);
        return new RealEstateTargetEdgeGraphResponse(
                targetId,
                normalizedDirection,
                service.publicGraph(targetId, normalizedDirection, edgeType, limit)
        );
    }

    @GetMapping("/internal/realestate/target-edges")
    public RealEstateTargetEdgeListResponse internalEdges(
            @RequestParam(required = false) String targetId,
            @RequestParam(defaultValue = "both") String direction,
            @RequestParam(required = false) String edgeType,
            @RequestParam(required = false) String reviewState,
            @RequestParam(defaultValue = "500") int limit
    ) {
        return new RealEstateTargetEdgeListResponse(
                service.internalEdges(targetId, normalizeDirection(direction), edgeType, reviewState, limit)
        );
    }

    private static String normalizeDirection(String value) {
        if ("in".equalsIgnoreCase(value) || "out".equalsIgnoreCase(value) || "both".equalsIgnoreCase(value)) {
            return value.toLowerCase();
        }
        return "both";
    }
}
