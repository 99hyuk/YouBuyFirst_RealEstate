package com.youbuyfirst.backend.realestate.dto;

public record RealEstateTargetUpsertBatchResponse(
        int acceptedTargets,
        int createdTargets,
        int updatedTargets,
        int skippedTargets
) {
}
