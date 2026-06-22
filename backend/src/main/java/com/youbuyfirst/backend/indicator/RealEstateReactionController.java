package com.youbuyfirst.backend.indicator;

import jakarta.validation.Valid;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;

@RestController
public class RealEstateReactionController {

    private final RealEstateReactionSnapshotService service;

    public RealEstateReactionController(RealEstateReactionSnapshotService service) {
        this.service = service;
    }

    @PostMapping("/internal/realestate/reaction-snapshots")
    public RealEstateReactionSnapshotBatchResponse upsert(
            @Valid @RequestBody RealEstateReactionSnapshotBatchRequest request
    ) {
        return new RealEstateReactionSnapshotBatchResponse(service.upsertAll(request.items()));
    }

    @GetMapping("/api/realestate/reactions/rankings")
    public RealEstateReactionRankingResponse rankings(
            @RequestParam(defaultValue = "region") String type,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant windowStart,
            @RequestParam(defaultValue = "60") int windowMinutes,
            @RequestParam(defaultValue = "20") int limit
    ) {
        if (windowMinutes <= 0 || windowMinutes > 10_080) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "windowMinutes must be between 1 and 10080");
        }
        if (windowStart == null) {
            return service.latestRanking(type, windowMinutes, limit);
        }
        return service.ranking(type, windowStart, windowMinutes, limit);
    }

    @GetMapping("/api/realestate/targets/{targetId}/reaction-snapshot")
    public RealEstateReactionSnapshotDetailResponse targetSnapshot(
            @PathVariable String targetId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant windowStart,
            @RequestParam(defaultValue = "60") int windowMinutes
    ) {
        if (windowMinutes <= 0 || windowMinutes > 10_080) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "windowMinutes must be between 1 and 10080");
        }
        return service.targetSnapshot(targetId, windowStart, windowMinutes);
    }

    @GetMapping("/api/realestate/targets/{targetId}/reaction-graph")
    public RealEstateReactionGraphResponse targetReactionGraph(
            @PathVariable String targetId,
            @RequestParam(defaultValue = "out") String direction,
            @RequestParam(required = false) String edgeType,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant windowStart,
            @RequestParam(defaultValue = "60") int windowMinutes,
            @RequestParam(defaultValue = "50") int limit
    ) {
        if (windowMinutes <= 0 || windowMinutes > 10_080) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "windowMinutes must be between 1 and 10080");
        }
        return service.targetReactionGraph(targetId, direction, edgeType, windowStart, windowMinutes, limit);
    }
}
