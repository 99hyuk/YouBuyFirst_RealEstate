package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record PolicyEventTargetRequest(
        @NotBlank @Size(max = 120) String targetId,
        @NotBlank @Size(max = 40) String impactType,
        Double confidence,
        @Size(max = 30) String reviewState
) {
}
