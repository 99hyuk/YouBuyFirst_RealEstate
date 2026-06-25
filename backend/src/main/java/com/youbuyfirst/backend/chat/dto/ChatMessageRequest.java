package com.youbuyfirst.backend.chat.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChatMessageRequest(
        @NotBlank @Size(max = 500) String body,
        @Size(max = 20) String displayName,
        @Valid ChatMessageAttachment attachment
) {
}
