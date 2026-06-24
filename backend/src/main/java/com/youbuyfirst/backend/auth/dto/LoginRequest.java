package com.youbuyfirst.backend.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record LoginRequest(
        @NotBlank @Pattern(regexp = "^[A-Za-z0-9]{4,20}$") String username,
        @NotBlank @Size(max = 100) String password
) {
}
