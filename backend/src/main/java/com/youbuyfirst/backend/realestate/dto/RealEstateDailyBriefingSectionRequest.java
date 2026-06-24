package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RealEstateDailyBriefingSectionRequest(
        @NotBlank @Size(max = 80) String sectionId,
        @NotBlank @Size(max = 120) String title,
        @NotBlank String body,
        Integer displayOrder
) {
}
