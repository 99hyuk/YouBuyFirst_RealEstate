package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record UserWatchTargetRequest(
        @NotBlank
        @Size(max = 30)
        String targetType,

        @NotBlank
        @Size(max = 160)
        String targetId,

        @NotBlank
        @Size(max = 120)
        String displayName,

        @NotBlank
        @Size(max = 600)
        String landingPath
) {
}
