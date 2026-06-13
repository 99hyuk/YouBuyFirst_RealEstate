package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.PolicyEventBatchRequest;
import com.youbuyfirst.backend.realestate.dto.PolicyEventBatchResponse;
import com.youbuyfirst.backend.realestate.dto.TimelineEventListResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateTimelineController {

    private final RealEstateTimelineService service;

    public RealEstateTimelineController(RealEstateTimelineService service) {
        this.service = service;
    }

    @PostMapping("/internal/realestate/policy-events")
    public PolicyEventBatchResponse upsertPolicyEvents(
            @Valid @RequestBody PolicyEventBatchRequest request
    ) {
        return service.upsertPolicyEvents(request.items());
    }

    @GetMapping("/api/realestate/targets/{targetId}/timeline")
    public TimelineEventListResponse targetTimeline(
            @PathVariable String targetId,
            @RequestParam(required = false) String eventType,
            @RequestParam(defaultValue = "50") int limit
    ) {
        return new TimelineEventListResponse(service.listTimeline(targetId, eventType, limit));
    }
}
