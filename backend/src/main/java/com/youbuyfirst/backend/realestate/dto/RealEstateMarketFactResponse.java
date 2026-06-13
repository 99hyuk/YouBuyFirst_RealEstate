package com.youbuyfirst.backend.realestate.dto;

import com.fasterxml.jackson.databind.JsonNode;

import java.time.Instant;
import java.time.LocalDate;

public record RealEstateMarketFactResponse(
        String targetType,
        String targetId,
        String factType,
        String provider,
        String providerDataset,
        String providerObjectId,
        String legalDongCode,
        LocalDate observedAt,
        LocalDate asOf,
        Instant ingestedAt,
        Instant sourceUpdatedAt,
        JsonNode valueJson,
        String dataStatus,
        boolean stale
) {
}
