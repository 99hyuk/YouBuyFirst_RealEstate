package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;

public record RealEstatePublicDataPromoteRequest(
        @Size(max = 100) String providerDataset,
        @Size(max = 180) String runKey,
        @Size(max = 30) String validationStatus,
        @Min(1) @Max(10_000) Integer limit
) {
}
