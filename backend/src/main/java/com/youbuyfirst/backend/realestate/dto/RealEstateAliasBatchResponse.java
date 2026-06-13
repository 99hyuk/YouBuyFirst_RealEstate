package com.youbuyfirst.backend.realestate.dto;

public record RealEstateAliasBatchResponse(
        int acceptedAliases,
        int createdAliases,
        int updatedAliases,
        int skippedAliases
) {
}
