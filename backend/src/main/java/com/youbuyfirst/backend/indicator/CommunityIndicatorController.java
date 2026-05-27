package com.youbuyfirst.backend.indicator;

import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;

@RestController
public class CommunityIndicatorController {

    private final CommunityIndicatorSnapshotService snapshotService;

    public CommunityIndicatorController(CommunityIndicatorSnapshotService snapshotService) {
        this.snapshotService = snapshotService;
    }

    @GetMapping("/api/indicators/community-snapshots")
    public CommunityIndicatorSnapshotResponse communitySnapshot(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant windowStart,
            @RequestParam(defaultValue = "30") int windowMinutes
    ) {
        if (windowMinutes <= 0 || windowMinutes > 10_080) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "windowMinutes must be between 1 and 10080");
        }
        return snapshotService.snapshot(windowStart, windowMinutes);
    }
}
