package com.youbuyfirst.backend.admin;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Size;

public record AliasCandidatePromoteRequest(
        @DecimalMin("0.0") @DecimalMax("1.0") Double confidence,
        @Size(max = 80) String reviewer,
        @Size(max = 500) String reviewNotes
) {
}
