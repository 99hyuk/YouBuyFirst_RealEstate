package com.youbuyfirst.backend.indicator;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RealEstateReactionSnapshotIssueRequest(
        @NotBlank @Size(max = 80) String issueKey,
        @NotBlank @Size(max = 80) String label,
        @DecimalMin("0.0") @DecimalMax("1.0") double share,
        @NotBlank @Size(max = 30) String direction,
        @Size(max = 500) String summary,
        @DecimalMin("0.0") @DecimalMax("1.0") double confidence
) {
}
