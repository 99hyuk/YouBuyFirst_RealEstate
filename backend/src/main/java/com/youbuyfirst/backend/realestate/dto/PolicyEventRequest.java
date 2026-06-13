package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.util.List;

public record PolicyEventRequest(
        @NotBlank @Size(max = 120) String eventId,
        @NotBlank @Size(max = 40) String eventType,
        @NotBlank @Size(max = 200) String title,
        @Size(max = 2000) String summary,
        @Size(max = 1000) String sourceUrl,
        Instant publishedAt,
        Instant effectiveFrom,
        Instant effectiveTo,
        @NotBlank @Size(max = 40) String targetScope,
        @NotBlank @Size(max = 30) String dataStatus,
        @NotEmpty List<@Valid PolicyEventTargetRequest> targets
) {
}
