package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateDailyBriefingBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateDailyBriefingBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateDailyBriefingResponse;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RealEstateDailyBriefingController {

    private final RealEstateDailyBriefingService service;

    public RealEstateDailyBriefingController(RealEstateDailyBriefingService service) {
        this.service = service;
    }

    @PostMapping("/internal/realestate/daily-briefings")
    public RealEstateDailyBriefingBatchResponse upsertDailyBriefings(
            @Valid @RequestBody RealEstateDailyBriefingBatchRequest request
    ) {
        return service.upsertAll(request.briefings());
    }

    @GetMapping("/api/realestate/daily-briefings/latest")
    public ResponseEntity<RealEstateDailyBriefingResponse> latestDailyBriefing() {
        return service.latest()
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.noContent().build());
    }
}
