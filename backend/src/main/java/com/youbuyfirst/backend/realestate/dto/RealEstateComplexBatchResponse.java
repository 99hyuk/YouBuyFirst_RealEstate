package com.youbuyfirst.backend.realestate.dto;

public record RealEstateComplexBatchResponse(
        int acceptedComplexes,
        int createdComplexes,
        int updatedComplexes,
        int skippedComplexes
) {
}
