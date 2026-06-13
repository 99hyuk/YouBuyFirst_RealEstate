package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RealEstateEvidenceItemRequest(
        @NotBlank @Size(max = 120) String evidenceItemId,
        @NotBlank @Size(max = 40) String evidenceType,
        @NotBlank @Size(max = 60) String refType,
        @NotBlank @Size(max = 120) String refId,
        @NotBlank @Size(max = 160) String label,
        @Size(max = 500) String valueText,
        @Size(max = 40) String severity
) {
}
