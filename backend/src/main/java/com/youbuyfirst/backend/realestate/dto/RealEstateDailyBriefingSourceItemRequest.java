package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RealEstateDailyBriefingSourceItemRequest(
        @NotBlank @Size(max = 160) String sourceItemId,
        @NotBlank @Size(max = 40) String sourceType,
        @Size(max = 160) String refId,
        @Size(max = 160) String label,
        @NotBlank @Size(max = 300) String title,
        @Size(max = 1000) String url,
        Integer displayOrder
) {
}
