package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.util.List;

public record RealEstateEvidenceLogRequest(
        @NotBlank @Size(max = 120) String evidenceLogId,
        @NotBlank @Size(max = 120) String targetId,
        Long snapshotId,
        @NotBlank @Size(max = 80) String evaluationVersion,
        @Size(max = 80) String promptVersion,
        @Size(max = 80) String modelName,
        @NotBlank @Size(max = 40) String tone,
        @NotBlank String summary,
        String subtitle,
        List<@Size(max = 160) String> caveats,
        @NotBlank @Size(max = 30) String dataQuality,
        Double confidence,
        @NotNull Instant evaluatedAt,
        @NotNull Instant asOf,
        @Size(max = 500) String skipReason,
        @NotNull List<@Valid RealEstateEvidenceItemRequest> evidenceItems
) {
}
