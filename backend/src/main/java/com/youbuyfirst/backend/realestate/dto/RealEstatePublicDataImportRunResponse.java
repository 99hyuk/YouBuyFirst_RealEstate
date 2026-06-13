package com.youbuyfirst.backend.realestate.dto;

import java.time.Instant;
import java.time.LocalDate;

public record RealEstatePublicDataImportRunResponse(
        Long id,
        String runKey,
        String providerDataset,
        String runType,
        LocalDate requestedFrom,
        LocalDate requestedTo,
        String status,
        long rowsSeen,
        long rowsLanded,
        long rowsStaged,
        long rowsPromoted,
        Instant startedAt,
        Instant finishedAt,
        String errorMessage
) {
}
