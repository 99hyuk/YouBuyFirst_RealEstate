package com.youbuyfirst.backend.indicator;

import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.util.List;

public record RealEstateReactionSnapshotRequest(
        @NotBlank @Size(max = 30) String targetType,
        @NotBlank @Size(max = 120) String targetId,
        @NotNull Instant windowStart,
        @NotNull Instant windowEnd,
        @NotNull Instant asOf,
        @Min(0) int mentionCount,
        @Min(0) int previousMentionCount,
        @Min(0) double expectationScore,
        @Min(0) double concernScore,
        @Min(0) double neutralScore,
        @Min(0) @Max(100) int heatScore,
        @DecimalMin("0.0") @DecimalMax("1.0") double confidence,
        @Min(0) int sourceCount,
        @DecimalMin("0.0") @DecimalMax("1.0") double sourceSkew,
        @NotBlank @Size(max = 30) String coverageStatus,
        boolean stale,
        List<@Valid RealEstateReactionSnapshotIssueRequest> issues
) {
}
