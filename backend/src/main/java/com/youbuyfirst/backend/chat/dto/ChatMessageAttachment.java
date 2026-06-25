package com.youbuyfirst.backend.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChatMessageAttachment(
        @NotBlank @Size(max = 20) String type,
        @NotBlank @Size(max = 80) String targetId,
        @NotBlank @Size(max = 80) String title,
        @Size(max = 120) String subtitle,
        @Size(max = 40) String metricLabel,
        @Size(max = 40) String metricValue,
        @Size(max = 10) String metricTone,
        @NotBlank @Size(max = 300) String landingPath
) {
}
