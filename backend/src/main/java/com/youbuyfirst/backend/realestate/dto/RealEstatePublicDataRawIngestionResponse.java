package com.youbuyfirst.backend.realestate.dto;

public record RealEstatePublicDataRawIngestionResponse(
        Long runId,
        int acceptedRawItems,
        int acceptedStagingItems
) {
}
