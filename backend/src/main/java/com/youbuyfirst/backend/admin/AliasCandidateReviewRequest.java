package com.youbuyfirst.backend.admin;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record AliasCandidateReviewRequest(
        @NotBlank String status,
        @Size(max = 80) String reviewer,
        @Size(max = 500) String reviewNotes
) {
}
